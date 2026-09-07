-- 数据库初始化脚本
-- 创建用户服务数据库（如果不存在）

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建业务隔离 schema（用户服务）
CREATE SCHEMA IF NOT EXISTS user_service;
ALTER SCHEMA user_service OWNER TO postgres;
GRANT USAGE, CREATE ON SCHEMA user_service TO postgres;

-- 注意：用户表和初始数据将由 SQLAlchemy 自动创建
-- 此脚本仅用于初始化数据库级别的设置

-- 创建只读用户（可选，用于监控）
-- CREATE USER readonly_user WITH PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE user_db TO readonly_user;
-- GRANT USAGE ON SCHEMA user_service TO readonly_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA user_service TO readonly_user;

-- 日志记录
DO $$
BEGIN
    RAISE NOTICE '数据库初始化完成 - %', NOW();
END $$;
