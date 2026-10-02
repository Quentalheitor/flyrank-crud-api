"""Week 4 - Assignment A7: Your first background job.

A small, self-contained FastAPI app:
  * POST /reports        -> answers 202 immediately and sends the event report/requested
  * GET  /reports/{id}   -> status endpoint (pending -> done / failed)
  * make-report          -> Inngest function (event trigger) that does the slow work
  * heartbeat            -> Inngest function (cron trigger) that logs a summary line

It does not use Supabase or Postgres, so it needs no .env file.

Run (from python-fastapi/):
    INNGEST_DEV=1 uvicorn background_job:app --port 8000
    npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest
"""
import logging
import uuid
from datetime import timedelta

import inngest
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from inngest import fast_api

reports: dict[str, dict] = {}

RETRIES = 2                 
MAX_ATTEMPTS = RETRIES + 1  

inngest_client = inngest.Inngest(
    app_id="report-api",
    logger=logging.getLogger("uvicorn"),
)


def build_report(report_id: str, attempt: int) -> str:
    report = reports.get(report_id)
    if report is None:
        return "unknown report, nothing to do"
    if report["status"] == "done":
        return "already built"
    if report["topic"] == "fail":
        if attempt >= MAX_ATTEMPTS - 1:
            report["status"] = "failed"
        raise RuntimeError("The report oven is broken!")
    report["result"] = f"Report data for {report['topic']}"
    report["status"] = "done"
    return "built"


def summarize_reports() -> str:
    counts = {"pending": 0, "done": 0, "failed": 0}
    for report in reports.values():
        counts[report["status"]] = counts.get(report["status"], 0) + 1
    return (
        f"heartbeat: total={len(reports)} pending={counts['pending']} "
        f"done={counts['done']} failed={counts['failed']}"
    )


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context) -> str:
    ctx.logger.info(ctx.event)
    await ctx.step.sleep("sleep-5-seconds", timedelta(seconds=5))
    return "Hello from the background!"


@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=RETRIES,
)
async def make_report(ctx: inngest.Context) -> str:
    report_id = ctx.event.data["id"]
    attempt = getattr(ctx, "attempt", 0)

    await ctx.step.sleep("do-the-slow-work", timedelta(seconds=8))

    def run_build() -> str:
        return build_report(report_id, getattr(ctx, "attempt", attempt))

    return await ctx.step.run("build-report", run_build)


@inngest_client.create_function(
    fn_id="heartbeat",
    trigger=inngest.TriggerCron(cron="* * * * *"),
)
async def heartbeat(ctx: inngest.Context) -> str:
    def log_summary() -> str:
        line = summarize_reports()
        ctx.logger.info(line)
        return line

    return await ctx.step.run("count-reports", log_summary)


app = FastAPI(title="A7 - background job")

fast_api.serve(app, inngest_client, [say_hello, make_report, heartbeat])


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": ".".join(str(p) for p in error["loc"] if p != "body"),
            "message": error["msg"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": errors})


@app.get("/")
def root():
    return {"message": "FlyRank background job API running", "version": "1.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/test-hello")
async def trigger_hello():
    ids = await inngest_client.send(
        inngest.Event(name="test/hello", data={"msg": "Hello!"})
    )
    return ids


@app.post("/reports")
async def create_report(body: dict):
    topic = body.get("topic")
    if not isinstance(topic, str) or topic.strip() == "":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "A non-empty 'topic' string is required"},
        )

    report_id = str(uuid.uuid4())
    topic = topic.strip()
    reports[report_id] = {"id": report_id, "topic": topic, "status": "pending"}
    try:
        await inngest_client.send(
            inngest.Event(name="report/requested", data={"id": report_id, "topic": topic})
        )
    except Exception:
        reports.pop(report_id, None)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Could not queue the report"},
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"id": report_id, "status": "pending"},
    )


@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    report = reports.get(report_id)
    if report is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Could not find report with matching id"},
        )
    return report