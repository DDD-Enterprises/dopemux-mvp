--
-- PostgreSQL database dump
--

\restrict JSmrarF0UVm3BYQsjnJ2t3UGl8JDOc4vF7UnWIyTwyw9IYsQaOWuaVQ98YY2XBa

-- Dumped from database version 16.10
-- Dumped by pg_dump version 16.10

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
-- Name: context; Type: SCHEMA; Schema: -; Owner: dopemux
--

CREATE SCHEMA context;


ALTER SCHEMA context OWNER TO dopemux;

--
-- Name: decisions; Type: SCHEMA; Schema: -; Owner: dopemux
--

CREATE SCHEMA decisions;


ALTER SCHEMA decisions OWNER TO dopemux;

--
-- Name: memory; Type: SCHEMA; Schema: -; Owner: dopemux
--

CREATE SCHEMA memory;


ALTER SCHEMA memory OWNER TO dopemux;

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
-- Name: auto_complete_progress(); Type: FUNCTION; Schema: public; Owner: dopemux
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


ALTER FUNCTION public.auto_complete_progress() OWNER TO dopemux;

--
-- Name: update_modified_column(); Type: FUNCTION; Schema: public; Owner: dopemux
--

CREATE FUNCTION public.update_modified_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_modified_column() OWNER TO dopemux;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: decisions; Type: TABLE; Schema: public; Owner: dopemux
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


ALTER TABLE public.decisions OWNER TO dopemux;

--
-- Name: progress_entries; Type: TABLE; Schema: public; Owner: dopemux
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


ALTER TABLE public.progress_entries OWNER TO dopemux;

--
-- Name: active_work; Type: VIEW; Schema: public; Owner: dopemux
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


ALTER VIEW public.active_work OWNER TO dopemux;

--
-- Name: entity_relationships; Type: TABLE; Schema: public; Owner: dopemux
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


ALTER TABLE public.entity_relationships OWNER TO dopemux;

--
-- Name: recent_activity; Type: VIEW; Schema: public; Owner: dopemux
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


ALTER VIEW public.recent_activity OWNER TO dopemux;

--
-- Name: search_cache; Type: TABLE; Schema: public; Owner: dopemux
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


ALTER TABLE public.search_cache OWNER TO dopemux;

--
-- Name: session_snapshots; Type: TABLE; Schema: public; Owner: dopemux
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


ALTER TABLE public.session_snapshots OWNER TO dopemux;

--
-- Name: workspace_contexts; Type: TABLE; Schema: public; Owner: dopemux
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


ALTER TABLE public.workspace_contexts OWNER TO dopemux;

--
-- Data for Name: decisions; Type: TABLE DATA; Schema: public; Owner: dopemux
--

COPY public.decisions (id, workspace_id, summary, rationale, alternatives, tags, confidence_level, decision_type, created_at, updated_at) FROM stdin;
85d95d8e-367c-4d09-9e01-b0e74faecbf9	dopemux-mvp	Implement hybrid database backend for ConPort persistence	Provides real ADHD memory persistence while maintaining current stability. Uses PostgreSQL for durability and Redis for fast 30-second auto-saves.	[]	{architecture,persistence,adhd-optimization}	medium	architecture	2025-09-29 04:11:40.006939+00	2025-09-29 04:11:40.006939+00
524e40f5-de40-41c5-9018-5ecc9e10f00b	dopemux-mvp	Enhanced ConPort Database Persistence Active	Successfully transitioned from mock data to real PostgreSQL + Redis persistence with ADHD-optimized auto-save and caching	[]	{persistence,adhd-optimization,database}	high	architecture	2025-09-29 04:16:21.314332+00	2025-09-29 04:16:21.314332+00
86ef7174-f08b-4de2-8c9c-f4f93404fe70	dopemux-mvp	Enhanced ConPort Real Persistence Active	Successfully implemented PostgreSQL + Redis persistence for ADHD memory. Context preservation now survives container restarts and interruptions.	[]	{persistence,adhd-optimization,success}	high	architecture	2025-09-29 04:17:55.677618+00	2025-09-29 04:17:55.677618+00
\.


--
-- Data for Name: entity_relationships; Type: TABLE DATA; Schema: public; Owner: dopemux
--

COPY public.entity_relationships (id, workspace_id, source_type, source_id, target_type, target_id, relationship_type, strength, created_at) FROM stdin;
\.


--
-- Data for Name: progress_entries; Type: TABLE DATA; Schema: public; Owner: dopemux
--

COPY public.progress_entries (id, workspace_id, description, status, percentage, linked_decision_id, priority, estimated_hours, actual_hours, created_at, updated_at, completed_at) FROM stdin;
e54dd5e3-090c-4a53-be7c-aa61b5914a08	dopemux-mvp	ConPort database persistence implementation	IN_PROGRESS	75	\N	high	\N	\N	2025-09-29 04:11:40.012675+00	2025-09-29 04:11:40.012675+00	\N
058dbd85-47dd-46d0-a51d-44fff81013de	dopemux-mvp	Enhanced ConPort Persistence Implementation	COMPLETED	100	\N	high	\N	\N	2025-09-29 04:18:16.458063+00	2025-09-29 04:18:16.458063+00	\N
\.


--
-- Data for Name: search_cache; Type: TABLE DATA; Schema: public; Owner: dopemux
--

COPY public.search_cache (id, workspace_id, query_text, query_hash, results, result_count, created_at, expires_at) FROM stdin;
\.


--
-- Data for Name: session_snapshots; Type: TABLE DATA; Schema: public; Owner: dopemux
--

COPY public.session_snapshots (id, workspace_id, session_start, session_end, focus_duration_minutes, interruption_count, tasks_completed, context_switches, session_quality, notes, created_at) FROM stdin;
\.


--
-- Data for Name: workspace_contexts; Type: TABLE DATA; Schema: public; Owner: dopemux
--

COPY public.workspace_contexts (id, workspace_id, active_context, last_activity, session_time, focus_state, session_milestone, created_at, updated_at) FROM stdin;
be581de1-44b4-4cc0-a1a0-1f3fc13cb4a3	dopemux-mvp	ADHD Memory System - Fully Operational	Database persistence validation complete	90 minutes	achievement mode	ConPort enhanced architecture success	2025-09-29 04:11:40.006367+00	2025-09-29 07:27:02.490926+00
\.


--
-- Name: decisions decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux
--

ALTER TABLE ONLY public.decisions
    ADD CONSTRAINT decisions_pkey PRIMARY KEY (id);


--
-- Name: entity_relationships entity_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_pkey PRIMARY KEY (id);


--
-- Name: progress_entries progress_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux
--

ALTER TABLE ONLY public.progress_entries
    ADD CONSTRAINT progress_entries_pkey PRIMARY KEY (id);


--
-- Name: search_cache search_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux
--

ALTER TABLE ONLY public.search_cache
    ADD CONSTRAINT search_cache_pkey PRIMARY KEY (id);


--
-- Name: session_snapshots session_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux
--

ALTER TABLE ONLY public.session_snapshots
    ADD CONSTRAINT session_snapshots_pkey PRIMARY KEY (id);


--
-- Name: workspace_contexts workspace_contexts_pkey; Type: CONSTRAINT; Schema: public; Owner: dopemux
--

ALTER TABLE ONLY public.workspace_contexts
    ADD CONSTRAINT workspace_contexts_pkey PRIMARY KEY (id);


--
-- Name: idx_decisions_created_at; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_decisions_created_at ON public.decisions USING btree (created_at DESC);


--
-- Name: idx_decisions_search; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_decisions_search ON public.decisions USING gin (to_tsvector('english'::regconfig, ((summary || ' '::text) || rationale)));


--
-- Name: idx_decisions_tags; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_decisions_tags ON public.decisions USING gin (tags);


--
-- Name: idx_decisions_type; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_decisions_type ON public.decisions USING btree (decision_type);


--
-- Name: idx_decisions_workspace_id; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_decisions_workspace_id ON public.decisions USING btree (workspace_id);


--
-- Name: idx_progress_created_at; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_progress_created_at ON public.progress_entries USING btree (created_at DESC);


--
-- Name: idx_progress_decision_link; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_progress_decision_link ON public.progress_entries USING btree (linked_decision_id);


--
-- Name: idx_progress_status; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_progress_status ON public.progress_entries USING btree (status);


--
-- Name: idx_progress_workspace_id; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_progress_workspace_id ON public.progress_entries USING btree (workspace_id);


--
-- Name: idx_relationships_source; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_relationships_source ON public.entity_relationships USING btree (source_type, source_id);


--
-- Name: idx_relationships_target; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_relationships_target ON public.entity_relationships USING btree (target_type, target_id);


--
-- Name: idx_relationships_type; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_relationships_type ON public.entity_relationships USING btree (relationship_type);


--
-- Name: idx_relationships_workspace_id; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_relationships_workspace_id ON public.entity_relationships USING btree (workspace_id);


--
-- Name: idx_search_cache_expires; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_search_cache_expires ON public.search_cache USING btree (expires_at);


--
-- Name: idx_search_cache_hash; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_search_cache_hash ON public.search_cache USING btree (workspace_id, query_hash);


--
-- Name: idx_sessions_start_time; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_sessions_start_time ON public.session_snapshots USING btree (session_start DESC);


--
-- Name: idx_sessions_workspace_id; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_sessions_workspace_id ON public.session_snapshots USING btree (workspace_id);


--
-- Name: idx_workspace_contexts_updated_at; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE INDEX idx_workspace_contexts_updated_at ON public.workspace_contexts USING btree (updated_at);


--
-- Name: idx_workspace_contexts_workspace_id; Type: INDEX; Schema: public; Owner: dopemux
--

CREATE UNIQUE INDEX idx_workspace_contexts_workspace_id ON public.workspace_contexts USING btree (workspace_id);


--
-- Name: progress_entries auto_complete_progress_trigger; Type: TRIGGER; Schema: public; Owner: dopemux
--

CREATE TRIGGER auto_complete_progress_trigger BEFORE UPDATE ON public.progress_entries FOR EACH ROW EXECUTE FUNCTION public.auto_complete_progress();


--
-- Name: decisions update_decisions_modtime; Type: TRIGGER; Schema: public; Owner: dopemux
--

CREATE TRIGGER update_decisions_modtime BEFORE UPDATE ON public.decisions FOR EACH ROW EXECUTE FUNCTION public.update_modified_column();


--
-- Name: progress_entries update_progress_modtime; Type: TRIGGER; Schema: public; Owner: dopemux
--

CREATE TRIGGER update_progress_modtime BEFORE UPDATE ON public.progress_entries FOR EACH ROW EXECUTE FUNCTION public.update_modified_column();


--
-- Name: workspace_contexts update_workspace_contexts_modtime; Type: TRIGGER; Schema: public; Owner: dopemux
--

CREATE TRIGGER update_workspace_contexts_modtime BEFORE UPDATE ON public.workspace_contexts FOR EACH ROW EXECUTE FUNCTION public.update_modified_column();


--
-- Name: progress_entries progress_entries_linked_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dopemux
--

ALTER TABLE ONLY public.progress_entries
    ADD CONSTRAINT progress_entries_linked_decision_id_fkey FOREIGN KEY (linked_decision_id) REFERENCES public.decisions(id);


--
-- PostgreSQL database dump complete
--

\unrestrict JSmrarF0UVm3BYQsjnJ2t3UGl8JDOc4vF7UnWIyTwyw9IYsQaOWuaVQ98YY2XBa

