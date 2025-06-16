CREATE TABLE users (
    id BIGINT PRIMARY KEY,                      -- Discord user ID, unique identifier
    discord_username TEXT NOT NULL,             -- Discord username (e.g., "Goomybot#1234")
    name TEXT,                                  -- User-selected display name (can be NULL)
    current_pokemon UUID,                       -- UUID of the currently selected Pokemon (Foreign Key to 'owned_pokemon', nullable)
    region TEXT NOT NULL,                       -- User's current region, determines available Pokemon
    frame BIGINT DEFAULT 0 NOT NULL,            -- Current frame for RNG calculations
    wallet BIGINT DEFAULT 0 NOT NULL CHECK (wallet >= 0), -- User's balance, non-negative
    level INT DEFAULT 1 NOT NULL,               -- User's (trainer's) level
    exp BIGINT DEFAULT 0 NOT NULL,              -- User's (trainer's) experience points
    next_exp BIGINT DEFAULT 0 NOT NULL,         -- Experience needed for the next level up
    tier_seed DOUBLE PRECISION NOT NULL,        -- RNG seed for Pokemon tier on frame
    type_seed DOUBLE PRECISION NOT NULL,        -- RNG seed for Pokemon type on frame
    pokemon_seed DOUBLE PRECISION NOT NULL,     -- RNG seed for specific Pokemon on frame
    shiny_seed DOUBLE PRECISION NOT NULL,       -- RNG seed for shininess
    item_seed DOUBLE PRECISION NOT NULL,        -- RNG seed for item drop on frame
    profile_image TEXT,                         -- URL for the user's profile picture (can be NULL)
    last_activity_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Last time the user interacted with the bot
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Date and time the user record was created
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL -- Last date and time the user record was modified
);

-- Optional: Add indexes for frequently queried columns to improve performance

-- Optional: Add an index for 'id'
CREATE INDEX idx_users_id ON users (id);

-- Optional: Add an index for 'region' if you frequently query users by region
-- CREATE INDEX idx_users_region ON users (region);


-- Table: public.user_pokemon

-- DROP TABLE IF EXISTS public.user_pokemon;

CREATE TABLE IF NOT EXISTS public.user_pokemon
(
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    user_id bigint NOT NULL,
    pokedex_id integer NOT NULL,
    name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    is_shiny boolean NOT NULL DEFAULT false,
    tier integer NOT NULL,
    types text[] COLLATE pg_catalog."default" NOT NULL DEFAULT '{}'::text[],
    ability character varying(255) COLLATE pg_catalog."default" NOT NULL,
    level integer NOT NULL,
    exp bigint NOT NULL DEFAULT 0,
    next_exp bigint NOT NULL DEFAULT 100,
    nature character varying(255) COLLATE pg_catalog."default" NOT NULL DEFAULT 'Hardy'::character varying,
    sprite_front text COLLATE pg_catalog."default" NOT NULL,
    sprite_back text COLLATE pg_catalog."default" NOT NULL,
    nickname character varying(255) COLLATE pg_catalog."default",
    original_user_id bigint,
    region character varying(255) COLLATE pg_catalog."default",
    gender character varying(50) COLLATE pg_catalog."default",
    ev jsonb NOT NULL DEFAULT '{}'::jsonb,
    iv jsonb NOT NULL DEFAULT '{}'::jsonb,
    held_item_id uuid,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    last_modified timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT user_pokemon_pkey PRIMARY KEY (id),
    CONSTRAINT user_pokemon_tier_check CHECK (tier >= 1 AND tier <= 4),
    CONSTRAINT user_pokemon_level_check CHECK (level >= 1 AND level <= 100)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.user_pokemon
    OWNER to postgres_admin;
-- Index: idx_pokemon_user_id

-- DROP INDEX IF EXISTS public.idx_pokemon_user_id;

CREATE INDEX IF NOT EXISTS idx_pokemon_user_id
    ON public.user_pokemon USING btree
    (user_id ASC NULLS LAST)
    TABLESPACE pg_default;