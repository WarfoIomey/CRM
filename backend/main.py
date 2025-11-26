from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from api.v1.router import api_router


app = FastAPI(title="CRM System")
app.include_router(api_router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"])
        errors.append(f"{field}: {error['msg']}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Ошибка валидации данных",
            "errors": errors 
        },
    )
