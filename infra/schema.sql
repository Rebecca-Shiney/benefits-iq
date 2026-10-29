SET XACT_ABORT ON;

IF OBJECT_ID(N'dbo.schema_migrations', N'U') IS NULL
CREATE TABLE dbo.schema_migrations(version int PRIMARY KEY, applied nvarchar(64) NOT NULL);

IF OBJECT_ID(N'dbo.cases', N'U') IS NULL
CREATE TABLE dbo.cases(
  id nvarchar(64) PRIMARY KEY, employer nvarchar(64) NOT NULL, member nvarchar(64) NOT NULL,
  scenario nvarchar(64) NOT NULL, state nvarchar(64) NOT NULL, version int NOT NULL,
  payload nvarchar(max) NOT NULL CHECK(ISJSON(payload)=1), brief nvarchar(max),
  decision nvarchar(max), expiry nvarchar(32)
);

IF OBJECT_ID(N'dbo.audit', N'U') IS NULL
CREATE TABLE dbo.audit(
  id bigint IDENTITY PRIMARY KEY, case_id nvarchar(64) NOT NULL REFERENCES dbo.cases(id),
  actor nvarchar(100) NOT NULL, event nvarchar(100) NOT NULL,
  trace nvarchar(100) NOT NULL, created nvarchar(64) NOT NULL
);

IF OBJECT_ID(N'dbo.decisions', N'U') IS NULL
CREATE TABLE dbo.decisions(
  [key] nvarchar(100) PRIMARY KEY, case_id nvarchar(64) NOT NULL REFERENCES dbo.cases(id),
  actor nvarchar(100) NOT NULL, fingerprint varchar(64) NOT NULL,
  response nvarchar(max) NOT NULL CHECK(ISJSON(response)=1)
);

IF OBJECT_ID(N'dbo.communications', N'U') IS NULL
CREATE TABLE dbo.communications(
  id bigint IDENTITY PRIMARY KEY, case_id nvarchar(64) NOT NULL REFERENCES dbo.cases(id),
  actor nvarchar(100) NOT NULL, text nvarchar(2000) NOT NULL, created nvarchar(64) NOT NULL
);

IF OBJECT_ID(N'dbo.briefs', N'U') IS NULL
CREATE TABLE dbo.briefs(
  case_id nvarchar(64) NOT NULL REFERENCES dbo.cases(id), version int NOT NULL,
  payload nvarchar(max) NOT NULL CHECK(ISJSON(payload)=1),
  actor nvarchar(100) NOT NULL, created nvarchar(64) NOT NULL,
  PRIMARY KEY(case_id,version)
);

IF OBJECT_ID(N'dbo.case_operations', N'U') IS NULL
CREATE TABLE dbo.case_operations(
  case_id nvarchar(64) PRIMARY KEY REFERENCES dbo.cases(id),
  received nvarchar(64) NOT NULL, target nvarchar(64) NOT NULL,
  priority nvarchar(32) NOT NULL, owner nvarchar(100) NOT NULL, channel nvarchar(100) NOT NULL
);

IF OBJECT_ID(N'dbo.tasks', N'U') IS NULL
CREATE TABLE dbo.tasks(
  id nvarchar(100) PRIMARY KEY, case_id nvarchar(64) NOT NULL REFERENCES dbo.cases(id),
  kind nvarchar(64) NOT NULL, role nvarchar(32) NOT NULL, state nvarchar(32) NOT NULL,
  due nvarchar(64) NOT NULL, version int NOT NULL, created nvarchar(64) NOT NULL,
  updated nvarchar(64) NOT NULL, actor nvarchar(100) NOT NULL
);

IF OBJECT_ID(N'dbo.source_records', N'U') IS NULL
CREATE TABLE dbo.source_records(
  kind nvarchar(32) NOT NULL, id nvarchar(200) NOT NULL, version nvarchar(100) NOT NULL,
  employer nvarchar(64), payload nvarchar(max) NOT NULL CHECK(ISJSON(payload)=1),
  content_hash varchar(64) NOT NULL, as_of nvarchar(64) NOT NULL, active bit NOT NULL,
  PRIMARY KEY(kind,id,version)
);

IF NOT EXISTS(SELECT 1 FROM sys.indexes WHERE name=N'one_active_source' AND object_id=OBJECT_ID(N'dbo.source_records'))
CREATE UNIQUE INDEX one_active_source ON dbo.source_records(kind,id) WHERE active=1;

IF OBJECT_ID(N'dbo.source_documents', N'U') IS NULL
CREATE TABLE dbo.source_documents(
  case_id nvarchar(64) PRIMARY KEY REFERENCES dbo.cases(id), source_id nvarchar(100) NOT NULL,
  version nvarchar(100) NOT NULL, content_hash varchar(64) NOT NULL,
  content varbinary(max) NOT NULL, as_of nvarchar(64) NOT NULL
);

IF OBJECT_ID(N'dbo.document_extractions', N'U') IS NULL
CREATE TABLE dbo.document_extractions(
  case_id nvarchar(64) NOT NULL REFERENCES dbo.cases(id), source_version nvarchar(100) NOT NULL,
  content_hash varchar(64) NOT NULL, model_id nvarchar(100) NOT NULL,
  payload nvarchar(max) NOT NULL CHECK(ISJSON(payload)=1), created nvarchar(64) NOT NULL,
  PRIMARY KEY(case_id,source_version,content_hash,model_id)
);

IF OBJECT_ID(N'dbo.portfolio_aggregates', N'U') IS NULL
CREATE TABLE dbo.portfolio_aggregates(
  employer nvarchar(64) NOT NULL, period nvarchar(64) NOT NULL,
  members int NOT NULL, specialty_utilizers int NOT NULL, cost decimal(18,2) NOT NULL,
  dataset nvarchar(100) NOT NULL, as_of nvarchar(64) NOT NULL,
  PRIMARY KEY(employer,period)
);
