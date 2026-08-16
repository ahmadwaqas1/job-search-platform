from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class WorkExperienceIn(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: str = ""


class WorkExperienceOut(WorkExperienceIn):
    id: UUID
    model_config = {"from_attributes": True}


class EducationIn(BaseModel):
    school: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_date: date | None = None
    end_date: date | None = None
    description: str = ""


class EducationOut(EducationIn):
    id: UUID
    model_config = {"from_attributes": True}


class CertificationIn(BaseModel):
    name: str = ""
    issuer: str = ""
    issue_date: date | None = None
    credential_url: str = ""


class CertificationOut(CertificationIn):
    id: UUID
    model_config = {"from_attributes": True}


class ProjectIn(BaseModel):
    name: str = ""
    description: str = ""
    url: str = ""
    technologies: str = ""


class ProjectOut(ProjectIn):
    id: UUID
    model_config = {"from_attributes": True}


class LanguageIn(BaseModel):
    name: str = ""
    proficiency: str = ""


class LanguageOut(LanguageIn):
    id: UUID
    model_config = {"from_attributes": True}


class SkillIn(BaseModel):
    name: str
    category: str = ""
    proficiency: str = ""


class SkillOut(SkillIn):
    id: UUID
    model_config = {"from_attributes": True}


class ProfileLinks(BaseModel):
    linkedin: str = ""
    github: str = ""
    website: str = ""
    other: str = ""


class ProfileIn(BaseModel):
    full_name: str = ""
    headline: str = ""
    summary: str = ""
    location: str = ""
    phone: str = ""
    email: str = ""
    links: ProfileLinks = Field(default_factory=ProfileLinks)
    work_experience: list[WorkExperienceIn] = Field(default_factory=list)
    education: list[EducationIn] = Field(default_factory=list)
    certifications: list[CertificationIn] = Field(default_factory=list)
    projects: list[ProjectIn] = Field(default_factory=list)
    languages: list[LanguageIn] = Field(default_factory=list)
    skills: list[SkillIn] = Field(default_factory=list)


class ProfileOut(BaseModel):
    id: UUID
    full_name: str
    headline: str
    summary: str
    location: str
    phone: str
    email: str
    links: dict
    work_experience: list[WorkExperienceOut]
    education: list[EducationOut]
    certifications: list[CertificationOut]
    projects: list[ProjectOut]
    languages: list[LanguageOut]
    skills: list[SkillOut]
    has_embedding: bool = False

    model_config = {"from_attributes": True}
