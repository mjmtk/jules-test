# core/api.py
import uuid
from ninja import NinjaAPI, Schema, Body
from ninja.errors import ValidationError as NinjaValidationError # Renamed to avoid clash
from django.http import HttpRequest, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from typing import List, Optional, Any
from datetime import date, datetime # Added datetime

from .models import Client, ClientStatus, Language, Pronoun, SexValue
from .schemas import (
    ReferenceDataResponseSchema, ClientInputSchema, ClientOutputSchema
)

# --- Custom Exceptions ---
class BaseAPIException(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"
    message: str = "An unexpected error occurred."
    details: Optional[dict] = None

    def __init__(self, message: Optional[str] = None, error_code: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message or self.message)
        if message:
            self.message = message
        if error_code:
            self.error_code = error_code
        if details:
            self.details = details

class InvalidReferenceError(BaseAPIException):
    status_code = 400
    error_code = "INVALID_REFERENCE"

class ClientNotFoundError(BaseAPIException):
    status_code = 404
    error_code = "CLIENT_NOT_FOUND"
    message = "Client not found."

class DuplicateEmailError(BaseAPIException):
    status_code = 409
    error_code = "DUPLICATE_EMAIL"
    message = "A client with this email address already exists."

class ValidationError(BaseAPIException): # Custom ValidationError to match PRD
    status_code = 400
    error_code = "VALIDATION_ERROR"
    message = "There were validation errors."


api = NinjaAPI()

# --- Exception Handlers ---
@api.exception_handler(BaseAPIException)
def base_api_exception_handler(request: HttpRequest, exc: BaseAPIException):
    return JsonResponse(
        {
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": "req_placeholder", # Placeholder
            }
        },
        status=exc.status_code,
    )

@api.exception_handler(NinjaValidationError) # Handles Pydantic validation errors
def pydantic_validation_error_handler(request: HttpRequest, exc: NinjaValidationError):
    details = {}
    for error in exc.errors:
        field = str(error["loc"][-1]) # Get the field name
        details[field] = error["msg"]
    
    return JsonResponse(
        {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "There were validation errors.",
                "details": details,
                "request_id": "req_placeholder",
            }
        },
        status=400, # Pydantic validation errors are typically 400
    )

@api.exception_handler(ObjectDoesNotExist) # Handles Django's ObjectDoesNotExist
def object_does_not_exist_handler(request: HttpRequest, exc: ObjectDoesNotExist):
    # This is a generic handler. Specific views might want to catch ObjectDoesNotExist
    # and raise a more specific error like ClientNotFoundError.
    return JsonResponse(
        {
            "error": {
                "code": "NOT_FOUND", # Generic not found
                "message": str(exc), # "Client matching query does not exist."
                "request_id": "req_placeholder",
            }
        },
        status=404,
    )


# --- Helper Functions ---
def get_fk_instance(model_class, code: Optional[str], field_name_for_error: str, allow_none: bool = False):
    if code is None:
        if allow_none:
            return None
        else: # Should not happen if schema enforces required code field, but good for defense
            raise InvalidReferenceError(details={field_name_for_error: f"{field_name_for_error.replace('_code','')} code cannot be null."})
    
    try:
        return model_class.objects.get(code=code)
    except ObjectDoesNotExist:
        raise InvalidReferenceError(details={field_name_for_error: f"Invalid {field_name_for_error.replace('_code','')} code provided: {code}"})


@api.get("/hello")
def hello(request):
    return {"message": "Hello, world!"}

@api.get("/reference-data/", response=ReferenceDataResponseSchema, summary="Get Reference Data")
def get_reference_data(request):
    """
    Retrieves all active reference data values (ClientStatus, Language, Pronoun, SexValue).
    This data is typically used to populate dropdowns or selection fields in client applications.
    """
    client_statuses = ClientStatus.objects.filter(is_active=True).order_by('display_order')
    languages = Language.objects.filter(is_active=True).order_by('display_order')
    pronouns = Pronoun.objects.filter(is_active=True).order_by('display_order')
    sex_values = SexValue.objects.filter(is_active=True).order_by('display_order')
    
    return {
        "client_statuses": list(client_statuses),
        "languages": list(languages),
        "pronouns": list(pronouns),
        "sex_values": list(sex_values),
    }

# --- Client Endpoints ---
DUMMY_USER_ID = uuid.UUID('00000000-0000-0000-0000-000000000000')

@api.post(
    "/clients/",
    response={201: ClientOutputSchema}, # Successful response
    # Error responses are handled by exception handlers, so no need to list every status code here
    # unless you want to override the default schema for a specific error.
    summary="Create a new client"
)
def create_client(request: HttpRequest, payload: ClientInputSchema):
    """
    Creates a new client record.
    - Validates input data, including reference codes.
    - Ensures that either email or phone is provided.
    - Checks for duplicate email addresses.
    """
    # Business Rule: At least one of email or phone must be provided.
    if not payload.email and not payload.phone:
        # Raise our custom ValidationError which will be caught by the base_api_exception_handler
        raise ValidationError(details={"__all__": "At least one of email or phone must be provided."})

    # Validate date_of_birth is not in the future
    if payload.date_of_birth > date.today():
        raise ValidationError(details={"date_of_birth": "Date of birth cannot be in the future."})

    # Check for duplicate email
    if payload.email:
        if Client.objects.filter(email__iexact=payload.email).exists():
            raise DuplicateEmailError(details={"email": f"A client with email '{payload.email}' already exists."})

    # Resolve foreign key codes to instances using the helper
    # The helper will raise InvalidReferenceError if a code is invalid.
    status_instance = get_fk_instance(ClientStatus, payload.status_code, 'status_code')
    language_instance = get_fk_instance(Language, payload.primary_language_code, 'primary_language_code', allow_none=True)
    pronoun_instance = get_fk_instance(Pronoun, payload.pronoun_code, 'pronoun_code', allow_none=True)
    sex_instance = get_fk_instance(SexValue, payload.sex_code, 'sex_code', allow_none=True)
    
    # Pydantic's schema validation (e.g. max_length for first_name) is handled by Ninja automatically.
    # If NinjaValidationError is raised, pydantic_validation_error_handler will format it.

    client_data = payload.dict(exclude_none=True, exclude={"status_code", "primary_language_code", "pronoun_code", "sex_code"})
    
    client = Client.objects.create(
        **client_data,
        status=status_instance,
        primary_language=language_instance,
        pronoun=pronoun_instance,
        sex=sex_instance,
        created_by=DUMMY_USER_ID, 
        updated_by=DUMMY_USER_ID  
    )
    return 201, client


@api.get(
    "/clients/{client_id}", 
    response={200: ClientOutputSchema}, # Successful response
    summary="Get client details by ID"
)
def get_client(request: HttpRequest, client_id: uuid.UUID):
    """
    Retrieves a specific client by their unique ID.
    Returns a 404 error if the client is not found.
    """
    try:
        # Use select_related to pre-fetch related objects for efficiency, 
        # as they will be needed by ClientOutputSchema
        client = Client.objects.select_related(
            'status', 'primary_language', 'pronoun', 'sex'
        ).get(id=client_id)
        return client
    except Client.DoesNotExist: # Catch Django's DoesNotExist
        # Raise our custom ClientNotFoundError, which will be handled
        raise ClientNotFoundError(details={"client_id": f"No client found with ID {client_id}"})


@api.put(
    "/clients/{client_id}",
    response={200: ClientOutputSchema},
    summary="Update a client (Full Update)"
)
def update_client(request: HttpRequest, client_id: uuid.UUID, payload: ClientInputSchema):
    """
    Updates an existing client record with all new data.
    - All fields in the payload are required for a PUT request by ClientInputSchema.
    - Validates input data, including reference codes.
    - Ensures that either email or phone is provided.
    - Checks for duplicate email addresses if the email is being changed.
    """
    try:
        client = Client.objects.get(id=client_id, deleted_at__isnull=True) # Ensure not soft-deleted
    except Client.DoesNotExist:
        raise ClientNotFoundError(details={"client_id": f"No client found with ID {client_id}"})

    # Business Rule: At least one of email or phone must be provided.
    if not payload.email and not payload.phone:
        raise ValidationError(details={"__all__": "At least one of email or phone must be provided."})

    # Validate date_of_birth is not in the future
    if payload.date_of_birth > date.today():
        raise ValidationError(details={"date_of_birth": "Date of birth cannot be in the future."})

    # Check for duplicate email if it's being changed
    if payload.email and payload.email.lower() != (client.email or '').lower():
        if Client.objects.filter(email__iexact=payload.email, deleted_at__isnull=True).exclude(id=client_id).exists():
            raise DuplicateEmailError(details={"email": f"A client with email '{payload.email}' already exists."})

    # Resolve foreign key codes to instances
    status_instance = get_fk_instance(ClientStatus, payload.status_code, 'status_code')
    language_instance = get_fk_instance(Language, payload.primary_language_code, 'primary_language_code', allow_none=True)
    pronoun_instance = get_fk_instance(Pronoun, payload.pronoun_code, 'pronoun_code', allow_none=True)
    sex_instance = get_fk_instance(SexValue, payload.sex_code, 'sex_code', allow_none=True)

    # Update client fields from payload
    # For PUT, all fields from ClientInputSchema are expected.
    client.first_name = payload.first_name
    client.last_name = payload.last_name
    client.date_of_birth = payload.date_of_birth
    client.email = payload.email
    client.phone = payload.phone
    client.interpreter_needed = payload.interpreter_needed
    
    client.status = status_instance
    client.primary_language = language_instance
    client.pronoun = pronoun_instance
    client.sex = sex_instance
    client.updated_by = DUMMY_USER_ID # Placeholder for user ID
    
    client.save()
    # Refresh from DB to ensure output schema gets all fields correctly, including resolved ones from FK relations
    client.refresh_from_db()
    return client


@api.patch(
    "/clients/{client_id}",
    response={200: ClientOutputSchema},
    summary="Partially update a client"
)
def patch_client(request: HttpRequest, client_id: uuid.UUID, payload: ClientInputSchema = Body(None, partial=True)):
    """
    Partially updates an existing client record.
    - Only provided fields in the payload will be updated.
    - Validates input data for provided fields, including reference codes.
    - If email or phone are updated, re-validates that at least one is present.
    - Checks for duplicate email addresses if the email is being changed.
    """
    try:
        client = Client.objects.get(id=client_id, deleted_at__isnull=True) # Ensure not soft-deleted
    except Client.DoesNotExist:
        raise ClientNotFoundError(details={"client_id": f"No client found with ID {client_id}"})

    payload_data = payload.dict(exclude_unset=True) # Get only fields that were actually sent

    if not payload_data:
        # As per common API behavior, PATCH with empty body can be a no-op returning 200,
        # or a 400 if some change is expected. Here, we'll treat it as no-op.
        # If you want to enforce at least one field, uncomment below:
        # raise ValidationError(details={"__all__": "No data provided for update."})
        return client # Return current client state if no data sent

    # Update fields present in the payload
    for attr, value in payload_data.items():
        if attr == "status_code":
            client.status = get_fk_instance(ClientStatus, value, 'status_code')
        elif attr == "primary_language_code":
            client.primary_language = get_fk_instance(Language, value, 'primary_language_code', allow_none=True)
        elif attr == "pronoun_code":
            client.pronoun = get_fk_instance(Pronoun, value, 'pronoun_code', allow_none=True)
        elif attr == "sex_code":
            client.sex = get_fk_instance(SexValue, value, 'sex_code', allow_none=True)
        elif attr == "date_of_birth":
            if value > date.today():
                raise ValidationError(details={"date_of_birth": "Date of birth cannot be in the future."})
            client.date_of_birth = value
        elif attr == "email":
            # Ensure email is not empty string if provided, treat as None if so (or validate in schema)
            processed_email = value if value else None 
            if processed_email and processed_email.lower() != (client.email or '').lower():
                if Client.objects.filter(email__iexact=processed_email, deleted_at__isnull=True).exclude(id=client_id).exists():
                    raise DuplicateEmailError(details={"email": f"A client with email '{processed_email}' already exists."})
            client.email = processed_email
        elif attr in ["first_name", "last_name", "phone", "interpreter_needed"]:
            setattr(client, attr, value)
        # Any other fields in ClientInputSchema that are not direct model fields or FK codes
        # should be handled or ignored here.

    # Post-update validation: At least one of email or phone must be provided.
    if not client.email and not client.phone:
        # This validation depends on whether email/phone were part of the PATCH payload.
        # If they were not, and the client already violated this, it might be complex.
        # For now, assume the client was valid before, so this check is if the PATCH made it invalid.
        raise ValidationError(details={"__all__": "Client must have at least one of email or phone after update."})

    client.updated_by = DUMMY_USER_ID # Placeholder
    client.save()
    
    # Refresh from DB to ensure output schema gets all fields correctly, especially FKs
    client.refresh_from_db()
    return client


@api.delete(
    "/clients/{client_id}",
    response={204: Any}, # No content response
    summary="Soft delete a client"
)
def delete_client(request: HttpRequest, client_id: uuid.UUID):
    """
    Soft deletes a client by:
    - Setting their status to 'deleted'.
    - Setting the 'deleted_at' timestamp.
    Returns a 204 No Content response on success.
    """
    try:
        client = Client.objects.get(id=client_id, deleted_at__isnull=True) # Ensure not already soft-deleted
    except Client.DoesNotExist:
        raise ClientNotFoundError(details={"client_id": f"No client found with ID {client_id}"})

    try:
        # Ensure 'deleted' status code exists
        deleted_status = ClientStatus.objects.get(code='deleted')
    except ClientStatus.DoesNotExist:
        # This is a server configuration issue if 'deleted' status is missing.
        raise BaseAPIException(
            message="Server configuration error: 'deleted' client status not found.",
            error_code="SERVER_CONFIG_ERROR",
            status_code=500
        )

    client.status = deleted_status
    client.deleted_at = datetime.now() # Use current timestamp for soft delete
    client.updated_by = DUMMY_USER_ID # Placeholder
    client.save(update_fields=['status', 'deleted_at', 'updated_by', 'updated_at']) # Be specific about fields to update
    
    return 204, None # Django Ninja expects a tuple for status code and body


# --- List and Search Endpoints ---

from ninja.pagination import paginate, LimitOffsetPagination
from ninja import Field
from django.db.models import Q

# For Ordering
from ninja.ordering import ordering, Ordering
from typing import List as TypingList # To avoid clash with List from typing

# For Age Calculation (will be used in search)
from dateutil.relativedelta import relativedelta
from django.utils import timezone


@api.get(
    "/clients/",
    response=TypingList[ClientOutputSchema], # Using TypingList for clarity
    summary="List and filter clients (Paginated)"
)
@paginate(LimitOffsetPagination, PageSchema=PaginatedResponse) # Use the custom PaginatedResponse
@ordering(Ordering, ordering_fields=['first_name', 'last_name', 'created_at', 'updated_at'])
def list_clients(
    request: HttpRequest,
    status: Optional[str] = Field(None, query=True, description="Filter by status code (e.g., active, inactive)"),
    language: Optional[str] = Field(None, query=True, description="Filter by primary language code (e.g., en-NZ)"),
    interpreter_needed: Optional[bool] = Field(None, query=True, description="Filter by interpreter needed (true/false)"),
    created_since: Optional[date] = Field(None, query=True, description="Filter by clients created since this ISO date"),
    updated_since: Optional[date] = Field(None, query=True, description="Filter by clients updated since this ISO date"),
    # Ordering is handled by the @ordering decorator
    # Pagination is handled by the @paginate decorator
):
    """
    Retrieves a list of clients with optional filtering, ordering, and pagination.
    - Soft-deleted clients are excluded.
    - Default limit for pagination is 50, max 200.
    """
    queryset = Client.objects.select_related(
        'status', 'primary_language', 'pronoun', 'sex'
    ).filter(deleted_at__isnull=True).exclude(status__code='deleted') # Exclude soft-deleted

    if status:
        queryset = queryset.filter(status__code__iexact=status)
    if language:
        queryset = queryset.filter(primary_language__code__iexact=language)
    if interpreter_needed is not None: # Check for None because it's a boolean
        queryset = queryset.filter(interpreter_needed=interpreter_needed)
    if created_since:
        queryset = queryset.filter(created_at__date__gte=created_since)
    if updated_since:
        queryset = queryset.filter(updated_at__date__gte=updated_since)
    
    # Ordering is applied automatically by the @ordering decorator based on query params
    # For example: ?ordering=last_name or ?ordering=-created_at
    # Pagination is applied automatically by the @paginate decorator
    
    return queryset


@api.get(
    "/clients/search",
    response=ClientSearchResponseSchema, # Custom schema for search results
    summary="Advanced search for clients"
)
def search_clients(
    request: HttpRequest,
    q: Optional[str] = Field(None, query=True, description="Search term for first_name, last_name, email, phone"),
    status: Optional[str] = Field(None, query=True, description="Filter by status code"),
    language: Optional[str] = Field(None, query=True, description="Filter by primary language code"),
    interpreter_needed: Optional[bool] = Field(None, query=True, description="Filter by interpreter needed"),
    age_min: Optional[int] = Field(None, query=True, ge=0, description="Minimum age in years"),
    age_max: Optional[int] = Field(None, query=True, ge=0, description="Maximum age in years"),
    limit: int = Field(20, query=True, ge=1, le=100, description="Number of results to return")
):
    """
    Performs an advanced search for clients based on multiple criteria.
    - Soft-deleted clients are excluded.
    - Search term 'q' queries across first_name, last_name, email, and phone.
    - Age filtering is based on current date.
    """
    queryset = Client.objects.select_related(
        'status', 'primary_language', 'pronoun', 'sex'
    ).filter(deleted_at__isnull=True).exclude(status__code='deleted') # Exclude soft-deleted

    if q:
        query_filter = (
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )
        queryset = queryset.filter(query_filter)
    
    if status:
        queryset = queryset.filter(status__code__iexact=status)
    if language:
        queryset = queryset.filter(primary_language__code__iexact=language)
    if interpreter_needed is not None:
        queryset = queryset.filter(interpreter_needed=interpreter_needed)

    today = timezone.now().date()
    if age_min is not None:
        # Clients who are at least age_min years old
        # Their birthday must be less than or equal to (today - age_min years)
        latest_birth_date_for_min_age = today - relativedelta(years=age_min)
        queryset = queryset.filter(date_of_birth__lte=latest_birth_date_for_min_age)
    
    if age_max is not None:
        # Clients who are at most age_max years old
        # Their birthday must be greater than (today - (age_max + 1) years)
        # This means they haven't had their (age_max + 1)-th birthday yet.
        earliest_birth_date_for_max_age = today - relativedelta(years=age_max + 1)
        queryset = queryset.filter(date_of_birth__gt=earliest_birth_date_for_max_age)

    # Apply limit
    results = list(queryset[:limit])
    
    return {
        "query": q,
        "count": len(results), # This is count of results returned, not total matching queryset.
                              # For total count, use queryset.count() before slicing,
                              # but be mindful of performance on large datasets for unindexed queries.
                              # PRD asks for count of results, so len(results) is fine.
        "results": results
    }
