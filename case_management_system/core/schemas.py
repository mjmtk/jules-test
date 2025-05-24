from ninja import ModelSchema, Schema
from typing import List, Optional, Any
from datetime import datetime
from .models import Client, ClientStatus, Language, Pronoun, SexValue

# Reference Data Schemas
class ClientStatusSchema(ModelSchema):
    class Meta:
        model = ClientStatus
        fields = "__all__"

class LanguageSchema(ModelSchema):
    class Meta:
        model = Language
        fields = "__all__"

class PronounSchema(ModelSchema):
    class Meta:
        model = Pronoun
        fields = "__all__"

class SexValueSchema(ModelSchema):
    class Meta:
        model = SexValue
        fields = "__all__"

class ReferenceDataResponseSchema(Schema):
    client_statuses: List[ClientStatusSchema]
    languages: List[LanguageSchema]
    pronouns: List[PronounSchema]
    sex_values: List[SexValueSchema]
    cache_expires_at: Optional[datetime] = None

# Client Schemas
class ClientInputSchema(ModelSchema):
    status_code: str
    primary_language_code: Optional[str] = None
    pronoun_code: Optional[str] = None
    sex_code: Optional[str] = None # maps to sex.code

    class Meta:
        model = Client
        fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "email",
            "phone",
            "interpreter_needed",
        ]
        # The foreign key fields (status, primary_language, pronoun, sex) are implicitly
        # excluded by not being listed in 'fields' and by having explicit code-based
        # fields (status_code, primary_language_code, etc.) defined in the schema.


class ClientOutputSchema(ModelSchema):
    status: ClientStatusSchema
    primary_language: Optional[LanguageSchema] = None
    pronoun: Optional[PronounSchema] = None
    sex: Optional[SexValueSchema] = None
    full_name: Optional[str] = None

    class Meta:
        model = Client
        fields = [
            "id",
            "first_name",
            "last_name",
            "date_of_birth",
            "email",
            "phone",
            "interpreter_needed",
            "created_at",
            "updated_at",
            "created_by", # Added as per model, will be UUID
            "updated_by", # Added as per model, will be UUID
            # Model foreign key fields are automatically handled by ModelSchema
            # and will use the nested schemas defined above if available
            "status",
            "primary_language",
            "pronoun",
            "sex",
        ]
        
    @staticmethod
    def resolve_full_name(obj: Client) -> Optional[str]:
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return None

# Pagination Schemas
class PaginatedResponse(Schema):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[Any] # This will be parameterized, e.g., list[ClientOutputSchema]

class ClientSearchResponseSchema(Schema):
    query: Optional[str] = None
    count: int
    results: List[ClientOutputSchema]
