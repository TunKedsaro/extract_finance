class AppError(Exception):
    """Base class for errors that can be returned safely by an adapter."""

    code = "application_error"
    status_code = 500
    default_message = "The extraction request could not be completed."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidInputPathError(AppError):
    code = "invalid_input_path"
    status_code = 400
    default_message = "input_path must identify a file inside the configured input directory."


class InputFileNotFoundError(AppError):
    code = "input_file_not_found"
    status_code = 404
    default_message = "The requested input file does not exist."


class UnsupportedDocumentTypeError(AppError):
    code = "unsupported_document_type"
    status_code = 415
    default_message = "Unsupported file type; use a PDF or XLSX file."


class InputFileTooLargeError(AppError):
    code = "input_file_too_large"
    status_code = 413
    default_message = "The input file exceeds the configured size limit."


class DocumentProcessingError(AppError):
    code = "document_processing_failed"
    status_code = 422
    default_message = "The input document could not be processed."


class ConfigurationError(AppError):
    code = "configuration_error"
    status_code = 500
    default_message = "The extraction service is not configured correctly."


class LLMServiceError(AppError):
    code = "llm_service_error"
    status_code = 502
    default_message = "The language model service could not complete the request."


class LLMResponseError(AppError):
    code = "invalid_llm_response"
    status_code = 502
    default_message = "The language model returned an invalid extraction result."


class OutputWriteError(AppError):
    code = "output_write_failed"
    status_code = 500
    default_message = "The extraction result could not be saved."
