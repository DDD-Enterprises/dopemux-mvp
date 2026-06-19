--
-- PostgreSQL database dump
--

\restrict IVpqsxurebt8AzhSaXqCcUUSDteQYL9avzbalBw6qg5k7Hk0EuVBTC3ygIKyk64

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg13+1)
-- Dumped by pg_dump version 16.10 (Debian 16.10-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: ag_catalog; Type: SCHEMA; Schema: -; Owner: dopemux_age
--

CREATE SCHEMA ag_catalog;


ALTER SCHEMA ag_catalog OWNER TO dopemux_age;

--
-- Name: knowledge_graph; Type: SCHEMA; Schema: -; Owner: dopemux_age
--

CREATE SCHEMA knowledge_graph;


ALTER SCHEMA knowledge_graph OWNER TO dopemux_age;

--
-- Name: age; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS age WITH SCHEMA ag_catalog;


--
-- Name: EXTENSION age; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION age IS 'AGE database extension';


--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: auto_complete_progress(); Type: FUNCTION; Schema: public; Owner: dopemux_age
--

CREATE FUNCTION public.auto_complete_progress() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.percentage = 100 AND OLD.percentage < 100 THEN
        NEW.status = 'COMPLETED';
        NEW.completed_at = NOW();
    ELSIF NEW.percentage < 100 AND OLD.status = 'COMPLETED' THEN
        NEW.status = 'IN_PROGRESS';
        NEW.completed_at = NULL;
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.auto_complete_progress() OWNER TO dopemux_age;

--
-- Name: update_modified_column(); Type: FUNCTION; Schema: public; Owner: dopemux_age
--

CREATE FUNCTION public.update_modified_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_modified_column() OWNER TO dopemux_age;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: _ag_label_edge; Type: TABLE; Schema: knowledge_graph; Owner: dopemux_age
--

CREATE TABLE knowledge_graph._ag_label_edge (
    id ag_catalog.graphid NOT NULL,
    start_id ag_catalog.graphid NOT NULL,
    end_id ag_catalog.graphid NOT NULL,
    properties ag_catalog.agtype DEFAULT ag_catalog.agtype_build_map() NOT NULL
);


ALTER TABLE knowledge_graph._ag_label_edge OWNER TO dopemux_age;

--
-- Name: _ag_label_edge_id_seq; Type: SEQUENCE; Schema: knowledge_graph; Owner: dopemux_age
--

CREATE SEQUENCE knowledge_graph._ag_label_edge_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 281474976710655
    CACHE 1;


ALTER SEQUENCE knowledge_graph._ag_label_edge_id_seq OWNER TO dopemux_age;

--
-- Name: _ag_label_edge_id_seq; Type: SEQUENCE OWNED BY; Schema: knowledge_graph; Owner: dopemux_age
--

ALTER SEQUENCE knowledge_graph._ag_label_edge_id_seq OWNED BY knowledge_graph._ag_label_edge.id;


--
-- Name: _ag_label_vertex; Type: TABLE; Schema: knowledge_graph; Owner: dopemux_age
--

CREATE TABLE knowledge_graph._ag_label_vertex (
    id ag_catalog.graphid NOT NULL,
    properties ag_catalog.agtype DEFAULT ag_catalog.agtype_build_map() NOT NULL
);


ALTER TABLE knowledge_graph._ag_label_vertex OWNER TO dopemux_age;

--
-- Name: _ag_label_vertex_id_seq; Type: SEQUENCE; Schema: knowledge_graph; Owner: dopemux_age
--

CREATE SEQUENCE knowledge_graph._ag_label_vertex_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 281474976710655
    CACHE 1;


ALTER SEQUENCE knowledge_graph._ag_label_vertex_id_seq OWNER TO dopemux_age;

--
-- Name: _ag_label_vertex_id_seq; Type: SEQUENCE OWNED BY; Schema: knowledge_graph; Owner: dopemux_age
--

ALTER SEQUENCE knowledge_graph._ag_label_vertex_id_seq OWNED BY knowledge_graph._ag_label_vertex.id;


--
-- Name: _label_id_seq; Type: SEQUENCE; Schema: knowledge_graph; Owner: dopemux_age
--

CREATE SEQUENCE knowledge_graph._label_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 65535
    CACHE 1
    CYCLE;


ALTER SEQUENCE knowledge_graph._label_id_seq OWNER TO dopemux_age;

--
-- Name: decisions; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.decisions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    workspace_id character varying(255) NOT NULL,
    summary text NOT NULL,
    rationale text NOT NULL,
    alternatives jsonb DEFAULT '[]'::jsonb,
    tags text[] DEFAULT '{}'::text[],
    confidence_level character varying(20) DEFAULT 'medium'::character varying,
    decision_type character varying(50) DEFAULT 'implementation'::character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.decisions OWNER TO dopemux_age;

--
-- Name: progress_entries; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.progress_entries (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    workspace_id character varying(255) NOT NULL,
    description text NOT NULL,
    status character varying(20) NOT NULL,
    percentage integer DEFAULT 0,
    linked_decision_id uuid,
    priority character varying(10) DEFAULT 'medium'::character varying,
    estimated_hours numeric(5,2),
    actual_hours numeric(5,2),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    CONSTRAINT progress_entries_percentage_check CHECK (((percentage >= 0) AND (percentage <= 100))),
    CONSTRAINT progress_entries_priority_check CHECK (((priority)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying, 'urgent'::character varying])::text[]))),
    CONSTRAINT progress_entries_status_check CHECK (((status)::text = ANY ((ARRAY['PLANNED'::character varying, 'IN_PROGRESS'::character varying, 'COMPLETED'::character varying, 'BLOCKED'::character varying, 'CANCELLED'::character varying])::text[])))
);


ALTER TABLE public.progress_entries OWNER TO dopemux_age;

--
-- Name: active_work; Type: VIEW; Schema: public; Owner: dopemux_age
--

CREATE VIEW public.active_work AS
 SELECT p.id,
    p.workspace_id,
    p.description,
    p.status,
    p.percentage,
    p.priority,
    p.created_at,
    d.summary AS related_decision,
    d.rationale AS decision_context
   FROM (public.progress_entries p
     LEFT JOIN public.decisions d ON ((p.linked_decision_id = d.id)))
  WHERE ((p.status)::text = ANY ((ARRAY['IN_PROGRESS'::character varying, 'PLANNED'::character varying])::text[]))
  ORDER BY
        CASE p.priority
            WHEN 'urgent'::text THEN 1
            WHEN 'high'::text THEN 2
            WHEN 'medium'::text THEN 3
            WHEN 'low'::text THEN 4
            ELSE NULL::integer
        END, p.created_at;


ALTER VIEW public.active_work OWNER TO dopemux_age;

--
-- Name: custom_data; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.custom_data (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    workspace_id character varying(255) NOT NULL,
    category character varying(100) NOT NULL,
    key character varying(255) NOT NULL,
    value jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.custom_data OWNER TO dopemux_age;

--
-- Name: ddg_decisions; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.ddg_decisions (
    id character varying NOT NULL,
    workspace_id character varying NOT NULL,
    instance_id character varying,
    summary text NOT NULL,
    tags json,
    source character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.ddg_decisions OWNER TO dopemux_age;

--
-- Name: ddg_embeddings; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.ddg_embeddings (
    id character varying NOT NULL,
    vector json NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.ddg_embeddings OWNER TO dopemux_age;

--
-- Name: ddg_progress; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.ddg_progress (
    id character varying NOT NULL,
    workspace_id character varying NOT NULL,
    instance_id character varying,
    status character varying NOT NULL,
    description text,
    percentage integer,
    source character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.ddg_progress OWNER TO dopemux_age;

--
-- Name: entity_relationships; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.entity_relationships (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    workspace_id character varying(255) NOT NULL,
    source_type character varying(50) NOT NULL,
    source_id uuid NOT NULL,
    target_type character varying(50) NOT NULL,
    target_id uuid NOT NULL,
    relationship_type character varying(50) NOT NULL,
    strength numeric(3,2) DEFAULT 1.0,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT entity_relationships_strength_check CHECK (((strength >= 0.0) AND (strength <= 1.0)))
);


ALTER TABLE public.entity_relationships OWNER TO dopemux_age;

--
-- Name: projects; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.projects (
    id character varying NOT NULL,
    instance_id character varying NOT NULL,
    name character varying NOT NULL,
    description text,
    status character varying NOT NULL,
    metadata json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.projects OWNER TO dopemux_age;

--
-- Name: recent_activity; Type: VIEW; Schema: public; Owner: dopemux_age
--

CREATE VIEW public.recent_activity AS
 SELECT 'decision'::text AS activity_type,
    decisions.id,
    decisions.workspace_id,
    decisions.summary AS description,
    decisions.created_at,
    'decision'::text AS icon
   FROM public.decisions
UNION ALL
 SELECT 'progress'::text AS activity_type,
    progress_entries.id,
    progress_entries.workspace_id,
    progress_entries.description,
    progress_entries.updated_at AS created_at,
        CASE progress_entries.status
            WHEN 'COMPLETED'::text THEN 'check'::text
            WHEN 'IN_PROGRESS'::text THEN 'clock'::text
            WHEN 'BLOCKED'::text THEN 'alert'::text
            ELSE 'task'::text
        END AS icon
   FROM public.progress_entries
  ORDER BY 5 DESC;


ALTER VIEW public.recent_activity OWNER TO dopemux_age;

--
-- Name: search_cache; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.search_cache (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    workspace_id character varying(255) NOT NULL,
    query_text text NOT NULL,
    query_hash character varying(64) NOT NULL,
    results jsonb NOT NULL,
    result_count integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone DEFAULT (now() + '01:00:00'::interval)
);


ALTER TABLE public.search_cache OWNER TO dopemux_age;

--
-- Name: session_snapshots; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.session_snapshots (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    workspace_id character varying(255) NOT NULL,
    session_start timestamp with time zone NOT NULL,
    session_end timestamp with time zone,
    focus_duration_minutes integer,
    interruption_count integer DEFAULT 0,
    tasks_completed integer DEFAULT 0,
    context_switches integer DEFAULT 0,
    session_quality character varying(20),
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT session_snapshots_session_quality_check CHECK (((session_quality)::text = ANY ((ARRAY['poor'::character varying, 'fair'::character varying, 'good'::character varying, 'excellent'::character varying])::text[])))
);


ALTER TABLE public.session_snapshots OWNER TO dopemux_age;

--
-- Name: tasks; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.tasks (
    id character varying NOT NULL,
    instance_id character varying NOT NULL,
    title character varying NOT NULL,
    description text,
    status character varying NOT NULL,
    priority character varying NOT NULL,
    project_id character varying,
    parent_task_id character varying,
    dependencies json,
    tags json,
    metadata json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    assigned_to character varying,
    estimated_hours integer
);


ALTER TABLE public.tasks OWNER TO dopemux_age;

--
-- Name: workspace_contexts; Type: TABLE; Schema: public; Owner: dopemux_age
--

CREATE TABLE public.workspace_contexts (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    workspace_id character varying(255) NOT NULL,
    active_context text,
    last_activity text,
    session_time character varying(50),
    focus_state character varying(50),
    session_milestone text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.workspace_contexts OWNER TO dopemux_age;

--
-- Name: _ag_label_edge id; Type: DEFAULT; Schema: knowledge_graph; Owner: dopemux_age
--

ALTER TABLE ONLY knowledge_graph._ag_label_edge ALTER COLUMN id SET DEFAULT ag_catalog._graphid((ag_catalog._label_id('knowledge_graph'::name, '_ag_label_edge'::name))::integer, nextval('knowledge_graph._ag_label_edge_id_seq'::regclass));


--
-- Name: _ag_label_vertex id; Type: DEFAULT; Schema: knowledge_graph; Owner: dopemux_age
--

ALTER TABLE ONLY knowledge_graph._ag_label_vertex ALTER COLUMN id SET DEFAULT ag_catalog._graphid((ag_catalog._label_id('knowledge_graph'::name, '_ag_label_vertex'::name))::integer, nextval('knowledge_graph._ag_label_vertex_id_seq'::regclass));


--
-- Name: _ag_label_edge _ag_label_edge_pkey; Type: CONSTRAINT; Schema: knowledge_graph; Owner: dopemux_age
--

ALTER TABLE ONLY knowledge_graph._ag_label_edge
    ADD CONSTRAINT _ag_label_edge_pkey PRIMARY KEY (id);


--
-- Name: _ag_label_vertex _ag_label_vertex_pkey; Type: CONSTRAINT; Schema: knowledge_graph; Owner: dopemux_age
--

ALTER TABLE ONLY knowledge_graph._ag_label_vertex
    ADD CONSTRAINT _ag_label_vertex_pkey PRIMARY KEY (id);


--
-- Name: custom_data custom_data_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.custom_data
    ADD CONSTRAINT custom_data_pkey PRIMARY KEY (id);


--
-- Name: custom_data custom_data_workspace_id_category_key_key; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.custom_data
    ADD CONSTRAINT custom_data_workspace_id_category_key_key UNIQUE (workspace_id, category, key);


--
-- Name: ddg_decisions ddg_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.ddg_decisions
    ADD CONSTRAINT ddg_decisions_pkey PRIMARY KEY (id);


--
-- Name: ddg_embeddings ddg_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.ddg_embeddings
    ADD CONSTRAINT ddg_embeddings_pkey PRIMARY KEY (id);


--
-- Name: ddg_progress ddg_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.ddg_progress
    ADD CONSTRAINT ddg_progress_pkey PRIMARY KEY (id);


--
-- Name: decisions decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.decisions
    ADD CONSTRAINT decisions_pkey PRIMARY KEY (id);


--
-- Name: entity_relationships entity_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_pkey PRIMARY KEY (id);


--
-- Name: progress_entries progress_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.progress_entries
    ADD CONSTRAINT progress_entries_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: search_cache search_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.search_cache
    ADD CONSTRAINT search_cache_pkey PRIMARY KEY (id);


--
-- Name: session_snapshots session_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.session_snapshots
    ADD CONSTRAINT session_snapshots_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: workspace_contexts workspace_contexts_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.workspace_contexts
    ADD CONSTRAINT workspace_contexts_pkey PRIMARY KEY (id);


--
-- Name: idx_custom_data_category; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_custom_data_category ON public.custom_data USING btree (category);


--
-- Name: idx_custom_data_key; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_custom_data_key ON public.custom_data USING btree (workspace_id, category, key);


--
-- Name: idx_custom_data_value; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_custom_data_value ON public.custom_data USING gin (value);


--
-- Name: idx_custom_data_workspace_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_custom_data_workspace_id ON public.custom_data USING btree (workspace_id);


--
-- Name: idx_decisions_created_at; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_decisions_created_at ON public.decisions USING btree (created_at DESC);


--
-- Name: idx_decisions_search; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_decisions_search ON public.decisions USING gin (to_tsvector('english'::regconfig, ((summary || ' '::text) || rationale)));


--
-- Name: idx_decisions_tags; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_decisions_tags ON public.decisions USING gin (tags);


--
-- Name: idx_decisions_type; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_decisions_type ON public.decisions USING btree (decision_type);


--
-- Name: idx_decisions_workspace_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_decisions_workspace_id ON public.decisions USING btree (workspace_id);


--
-- Name: idx_progress_created_at; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_progress_created_at ON public.progress_entries USING btree (created_at DESC);


--
-- Name: idx_progress_decision_link; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_progress_decision_link ON public.progress_entries USING btree (linked_decision_id);


--
-- Name: idx_progress_status; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_progress_status ON public.progress_entries USING btree (status);


--
-- Name: idx_progress_workspace_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_progress_workspace_id ON public.progress_entries USING btree (workspace_id);


--
-- Name: idx_relationships_source; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_relationships_source ON public.entity_relationships USING btree (source_type, source_id);


--
-- Name: idx_relationships_target; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_relationships_target ON public.entity_relationships USING btree (target_type, target_id);


--
-- Name: idx_relationships_type; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_relationships_type ON public.entity_relationships USING btree (relationship_type);


--
-- Name: idx_relationships_workspace_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_relationships_workspace_id ON public.entity_relationships USING btree (workspace_id);


--
-- Name: idx_search_cache_expires; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_search_cache_expires ON public.search_cache USING btree (expires_at);


--
-- Name: idx_search_cache_hash; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_search_cache_hash ON public.search_cache USING btree (workspace_id, query_hash);


--
-- Name: idx_sessions_start_time; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_sessions_start_time ON public.session_snapshots USING btree (session_start DESC);


--
-- Name: idx_sessions_workspace_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_sessions_workspace_id ON public.session_snapshots USING btree (workspace_id);


--
-- Name: idx_workspace_contexts_updated_at; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX idx_workspace_contexts_updated_at ON public.workspace_contexts USING btree (updated_at);


--
-- Name: idx_workspace_contexts_workspace_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE UNIQUE INDEX idx_workspace_contexts_workspace_id ON public.workspace_contexts USING btree (workspace_id);


--
-- Name: ix_ddg_decisions_instance_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX ix_ddg_decisions_instance_id ON public.ddg_decisions USING btree (instance_id);


--
-- Name: ix_ddg_decisions_workspace_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX ix_ddg_decisions_workspace_id ON public.ddg_decisions USING btree (workspace_id);


--
-- Name: ix_ddg_progress_instance_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX ix_ddg_progress_instance_id ON public.ddg_progress USING btree (instance_id);


--
-- Name: ix_ddg_progress_workspace_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX ix_ddg_progress_workspace_id ON public.ddg_progress USING btree (workspace_id);


--
-- Name: ix_projects_instance_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX ix_projects_instance_id ON public.projects USING btree (instance_id);


--
-- Name: ix_tasks_instance_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX ix_tasks_instance_id ON public.tasks USING btree (instance_id);


--
-- Name: ix_tasks_parent_task_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX ix_tasks_parent_task_id ON public.tasks USING btree (parent_task_id);


--
-- Name: ix_tasks_project_id; Type: INDEX; Schema: public; Owner: dopemux_age
--

CREATE INDEX ix_tasks_project_id ON public.tasks USING btree (project_id);


--
-- Name: progress_entries auto_complete_progress_trigger; Type: TRIGGER; Schema: public; Owner: dopemux_age
--

CREATE TRIGGER auto_complete_progress_trigger BEFORE UPDATE ON public.progress_entries FOR EACH ROW EXECUTE FUNCTION public.auto_complete_progress();


--
-- Name: decisions update_decisions_modtime; Type: TRIGGER; Schema: public; Owner: dopemux_age
--

CREATE TRIGGER update_decisions_modtime BEFORE UPDATE ON public.decisions FOR EACH ROW EXECUTE FUNCTION public.update_modified_column();


--
-- Name: progress_entries update_progress_modtime; Type: TRIGGER; Schema: public; Owner: dopemux_age
--

CREATE TRIGGER update_progress_modtime BEFORE UPDATE ON public.progress_entries FOR EACH ROW EXECUTE FUNCTION public.update_modified_column();


--
-- Name: workspace_contexts update_workspace_contexts_modtime; Type: TRIGGER; Schema: public; Owner: dopemux_age
--

CREATE TRIGGER update_workspace_contexts_modtime BEFORE UPDATE ON public.workspace_contexts FOR EACH ROW EXECUTE FUNCTION public.update_modified_column();


--
-- Name: progress_entries progress_entries_linked_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dopemux_age
--

ALTER TABLE ONLY public.progress_entries
    ADD CONSTRAINT progress_entries_linked_decision_id_fkey FOREIGN KEY (linked_decision_id) REFERENCES public.decisions(id);


--
-- PostgreSQL database dump complete
--

\unrestrict IVpqsxurebt8AzhSaXqCcUUSDteQYL9avzbalBw6qg5k7Hk0EuVBTC3ygIKyk64
