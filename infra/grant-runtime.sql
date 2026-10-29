DECLARE @clientId uniqueidentifier = CAST(? AS uniqueidentifier);
DECLARE @sid varbinary(16) = CONVERT(varbinary(16), @clientId);
IF USER_ID(N'benefits_runtime') IS NULL
BEGIN
    DECLARE @create nvarchar(max) =
        N'CREATE USER [benefits_runtime] WITH SID = ' +
        CONVERT(varchar(max), @sid, 1) + N', TYPE = E;';
    EXEC(@create);
END;
IF NOT EXISTS(
    SELECT 1 FROM sys.database_principals
    WHERE name=N'benefits_runtime' AND sid=@sid AND authentication_type_desc=N'EXTERNAL'
)
    THROW 51000, 'RUNTIME_SQL_IDENTITY_COLLISION', 1;
IF EXISTS(
    SELECT 1 FROM sys.database_role_members
    WHERE member_principal_id=USER_ID(N'benefits_runtime')
)
    THROW 51001, 'RUNTIME_SQL_ROLE_MEMBERSHIP_REQUIRES_REVIEW', 1;

GRANT SELECT ON dbo.schema_migrations TO benefits_runtime;
GRANT SELECT, UPDATE ON dbo.cases TO benefits_runtime;
GRANT SELECT, INSERT ON dbo.audit TO benefits_runtime;
GRANT SELECT, INSERT ON dbo.decisions TO benefits_runtime;
GRANT SELECT, INSERT ON dbo.communications TO benefits_runtime;
GRANT SELECT, INSERT ON dbo.briefs TO benefits_runtime;
GRANT SELECT, UPDATE ON dbo.case_operations TO benefits_runtime;
GRANT SELECT, INSERT, UPDATE ON dbo.tasks TO benefits_runtime;
GRANT SELECT, INSERT ON dbo.document_extractions TO benefits_runtime;
GRANT SELECT ON dbo.source_records TO benefits_runtime;
GRANT SELECT ON dbo.source_documents TO benefits_runtime;
GRANT SELECT ON dbo.portfolio_aggregates TO benefits_runtime;

DENY INSERT, UPDATE, DELETE ON dbo.schema_migrations TO benefits_runtime;
DENY INSERT, DELETE ON dbo.cases TO benefits_runtime;
DENY UPDATE, DELETE ON dbo.audit TO benefits_runtime;
DENY UPDATE, DELETE ON dbo.decisions TO benefits_runtime;
DENY UPDATE, DELETE ON dbo.communications TO benefits_runtime;
DENY UPDATE, DELETE ON dbo.briefs TO benefits_runtime;
DENY INSERT, DELETE ON dbo.case_operations TO benefits_runtime;
DENY DELETE ON dbo.tasks TO benefits_runtime;
DENY UPDATE, DELETE ON dbo.document_extractions TO benefits_runtime;
DENY INSERT, UPDATE, DELETE ON dbo.source_records TO benefits_runtime;
DENY INSERT, UPDATE, DELETE ON dbo.source_documents TO benefits_runtime;
DENY INSERT, UPDATE, DELETE ON dbo.portfolio_aggregates TO benefits_runtime;
DENY CREATE TABLE, ALTER ANY USER, ALTER ANY ROLE TO benefits_runtime;
