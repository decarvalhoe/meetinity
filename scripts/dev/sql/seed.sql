-- Données de démonstration pour l'environnement de développement Meetinity
-- Le script est idempotent : les exécutions successives mettent à jour les enregistrements existants.

\echo 'Chargement des catégories et tags d\'événements'
INSERT INTO event_categories (id, name, description)
VALUES
    (100, 'Tech Talks', 'Sessions techniques et partages d\'expérience'),
    (101, 'Networking', 'Moments dédiés aux rencontres informelles'),
    (102, 'Product Discovery', 'Ateliers centrés sur l\'expérience produit')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

INSERT INTO event_tags (id, name)
VALUES
    (200, 'python'),
    (201, 'design'),
    (202, 'growth')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    updated_at = NOW();

\echo 'Chargement des modèles et séries d\'événements'
INSERT INTO event_templates (id, name, description, default_duration_minutes, default_timezone, default_locale)
VALUES
    (300, 'Meetup standard', 'Template pour les meetups communautaires', 120, 'Europe/Paris', 'fr'),
    (301, 'Webinar expert', 'Format 60 minutes orienté expertise', 60, 'Europe/Paris', 'fr')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    default_duration_minutes = EXCLUDED.default_duration_minutes,
    default_timezone = EXCLUDED.default_timezone,
    default_locale = EXCLUDED.default_locale,
    updated_at = NOW();

INSERT INTO event_series (id, name, description)
VALUES
    (400, 'Les Rendez-vous Produit', 'Série dédiée aux Product Managers'),
    (401, 'Tech Leaders Lab', 'Rencontres techniques trimestrielles')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

\echo 'Chargement des événements'
INSERT INTO events (
    id, title, description, event_date, location, event_type, attendees,
    registration_open, registration_deadline, timezone, status, event_format,
    streaming_url, capacity_limit, default_locale, fallback_locale,
    organizer_email, settings, template_id, series_id
)
VALUES
    (
        500,
        'Meetinity Community Night',
        'Rencontre physique des membres de la communauté Meetinity.',
        CURRENT_DATE + INTERVAL '14 days',
        'Station F, Paris',
        'community',
        48,
        TRUE,
        CURRENT_TIMESTAMP + INTERVAL '12 days',
        'Europe/Paris',
        'approved',
        'in_person',
        NULL,
        120,
        'fr',
        'en',
        'events@meetinity.com',
        '{"livestream": false, "badge": true}'::jsonb,
        300,
        400
    ),
    (
        501,
        'Product Discovery Clinic',
        'Atelier virtuel pour analyser des retours utilisateurs et prioriser la roadmap.',
        CURRENT_DATE + INTERVAL '21 days',
        'En ligne',
        'workshop',
        36,
        TRUE,
        CURRENT_TIMESTAMP + INTERVAL '20 days',
        'Europe/Paris',
        'approved',
        'virtual',
        'https://meetinity.example.com/webinars/discovery-clinic',
        250,
        'fr',
        'en',
        'product@meetinity.com',
        '{"livestream": true, "replay": true}'::jsonb,
        301,
        401
    )
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    event_date = EXCLUDED.event_date,
    location = EXCLUDED.location,
    event_type = EXCLUDED.event_type,
    attendees = EXCLUDED.attendees,
    registration_open = EXCLUDED.registration_open,
    registration_deadline = EXCLUDED.registration_deadline,
    timezone = EXCLUDED.timezone,
    status = EXCLUDED.status,
    event_format = EXCLUDED.event_format,
    streaming_url = EXCLUDED.streaming_url,
    capacity_limit = EXCLUDED.capacity_limit,
    default_locale = EXCLUDED.default_locale,
    fallback_locale = EXCLUDED.fallback_locale,
    organizer_email = EXCLUDED.organizer_email,
    settings = EXCLUDED.settings,
    template_id = EXCLUDED.template_id,
    series_id = EXCLUDED.series_id,
    updated_at = NOW();

INSERT INTO event_categories_events (event_id, category_id)
VALUES
    (500, 100),
    (500, 101),
    (501, 101),
    (501, 102)
ON CONFLICT (event_id, category_id) DO NOTHING;

INSERT INTO event_tags_events (event_id, tag_id)
VALUES
    (500, 200),
    (501, 201),
    (501, 202)
ON CONFLICT (event_id, tag_id) DO NOTHING;

\echo 'Chargement des utilisateurs de test'
INSERT INTO users (
    id, email, name, provider, provider_user_id, location, industry, title,
    company, timezone, is_active, last_login, last_active_at, login_count,
    engagement_score, reputation_score, profile_completeness, trust_score,
    privacy_level, created_at, updated_at
)
VALUES
    (
        9000,
        'alice.martin@example.com',
        'Alice Martin',
        'google',
        'alice-google-123',
        'Paris, France',
        'Product',
        'Lead PM',
        'Meetinity',
        'Europe/Paris',
        TRUE,
        NOW() - INTERVAL '1 day',
        NOW() - INTERVAL '2 hours',
        12,
        78,
        64,
        92,
        80,
        'standard',
        NOW() - INTERVAL '120 days',
        NOW()
    ),
    (
        9001,
        'bruno.leroy@example.com',
        'Bruno Leroy',
        'linkedin',
        'bruno-linkedin-987',
        'Lyon, France',
        'Engineering',
        'Engineering Manager',
        'Meetinity',
        'Europe/Paris',
        TRUE,
        NOW() - INTERVAL '2 days',
        NOW() - INTERVAL '30 minutes',
        25,
        88,
        71,
        85,
        77,
        'standard',
        NOW() - INTERVAL '200 days',
        NOW()
    ),
    (
        9002,
        'claire.dupont@example.com',
        'Claire Dupont',
        'google',
        'claire-google-654',
        'Remote',
        'Design',
        'UX Researcher',
        'Freelance',
        'Europe/Paris',
        TRUE,
        NOW() - INTERVAL '5 days',
        NOW() - INTERVAL '1 day',
        8,
        66,
        58,
        70,
        65,
        'standard',
        NOW() - INTERVAL '90 days',
        NOW()
    )
ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    name = EXCLUDED.name,
    provider = EXCLUDED.provider,
    provider_user_id = EXCLUDED.provider_user_id,
    location = EXCLUDED.location,
    industry = EXCLUDED.industry,
    title = EXCLUDED.title,
    company = EXCLUDED.company,
    timezone = EXCLUDED.timezone,
    is_active = EXCLUDED.is_active,
    last_login = EXCLUDED.last_login,
    last_active_at = EXCLUDED.last_active_at,
    login_count = EXCLUDED.login_count,
    engagement_score = EXCLUDED.engagement_score,
    reputation_score = EXCLUDED.reputation_score,
    profile_completeness = EXCLUDED.profile_completeness,
    trust_score = EXCLUDED.trust_score,
    updated_at = NOW();

\echo 'Chargement des profils de matching'
INSERT INTO matching.users (
    id, email, full_name, title, company, bio, preferences, is_active, created_at, updated_at
)
VALUES
    (
        9000,
        'alice.martin@example.com',
        'Alice Martin',
        'Lead PM',
        'Meetinity',
        'Experte produit passionnée par les communautés SaaS.',
        '[{"type":"skills","value":["product","leadership","ai"]},{"type":"objectives","value":["networking","mentorat"]}]'::jsonb,
        TRUE,
        timezone('UTC', now()) - INTERVAL '120 days',
        timezone('UTC', now())
    ),
    (
        9001,
        'bruno.leroy@example.com',
        'Bruno Leroy',
        'Engineering Manager',
        'Meetinity',
        'Manager technique encadrant des équipes distribuées.',
        '[{"type":"skills","value":["cloud","kafka","python"]},{"type":"connections","value":["product","devops"]}]'::jsonb,
        TRUE,
        timezone('UTC', now()) - INTERVAL '200 days',
        timezone('UTC', now())
    ),
    (
        9002,
        'claire.dupont@example.com',
        'Claire Dupont',
        'UX Researcher',
        'Freelance',
        'Spécialiste de la recherche utilisateur et du design inclusif.',
        '[{"type":"skills","value":["ux","recherche","facilitation"]},{"type":"objectives","value":["co-création","partage"]}]'::jsonb,
        TRUE,
        timezone('UTC', now()) - INTERVAL '90 days',
        timezone('UTC', now())
    )
ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    title = EXCLUDED.title,
    company = EXCLUDED.company,
    bio = EXCLUDED.bio,
    preferences = EXCLUDED.preferences,
    is_active = EXCLUDED.is_active,
    updated_at = timezone('UTC', now());

SELECT setval('matching.users_id_seq', (SELECT MAX(id) FROM matching.users));

INSERT INTO matching.swipes (id, user_id, target_id, action, created_at)
VALUES
    (
        6000,
        9000,
        9001,
        'like',
        timezone('UTC', now()) - INTERVAL '2 days'
    ),
    (
        6001,
        9001,
        9000,
        'like',
        timezone('UTC', now()) - INTERVAL '1 day'
    ),
    (
        6002,
        9002,
        9000,
        'pass',
        timezone('UTC', now()) - INTERVAL '3 days'
    )
ON CONFLICT (id) DO UPDATE SET
    user_id = EXCLUDED.user_id,
    target_id = EXCLUDED.target_id,
    action = EXCLUDED.action,
    created_at = EXCLUDED.created_at;

SELECT setval('matching.swipes_id_seq', (SELECT MAX(id) FROM matching.swipes));

INSERT INTO matching.matches (id, user_id, matched_user_id, created_at)
VALUES
    (
        7000,
        9000,
        9001,
        timezone('UTC', now()) - INTERVAL '1 day'
    ),
    (
        7001,
        9001,
        9000,
        timezone('UTC', now()) - INTERVAL '1 day'
    )
ON CONFLICT (user_id, matched_user_id) DO UPDATE SET
    created_at = EXCLUDED.created_at;

SELECT setval('matching.matches_id_seq', (SELECT MAX(id) FROM matching.matches));

INSERT INTO matching.match_scores (id, match_id, score, details, created_at)
VALUES
    (
        7100,
        7000,
        87.5,
        '{"common_interests":["product","meetups"]}'::jsonb,
        timezone('UTC', now()) - INTERVAL '1 day'
    ),
    (
        7101,
        7001,
        87.5,
        '{"common_interests":["product","mentorat"]}'::jsonb,
        timezone('UTC', now()) - INTERVAL '1 day'
    )
ON CONFLICT (match_id) DO UPDATE SET
    score = EXCLUDED.score,
    details = EXCLUDED.details,
    created_at = EXCLUDED.created_at;

SELECT setval('matching.match_scores_id_seq', (SELECT MAX(id) FROM matching.match_scores));

INSERT INTO matching.swipe_events (id, swipe_id, event_type, user_id, target_id, action, score, payload, created_at)
VALUES
    (
        8000,
        6000,
        'swipe',
        9000,
        9001,
        'like',
        87.5,
        '{"is_match": true, "common_interests": ["product","meetups"]}'::jsonb,
        timezone('UTC', now()) - INTERVAL '1 day'
    ),
    (
        8001,
        6002,
        'swipe',
        9002,
        9000,
        'pass',
        NULL,
        '{"notes": "Pas d'intérêt commun identifié"}'::jsonb,
        timezone('UTC', now()) - INTERVAL '3 days'
    )
ON CONFLICT (id) DO UPDATE SET
    swipe_id = EXCLUDED.swipe_id,
    event_type = EXCLUDED.event_type,
    user_id = EXCLUDED.user_id,
    target_id = EXCLUDED.target_id,
    action = EXCLUDED.action,
    score = EXCLUDED.score,
    payload = EXCLUDED.payload,
    created_at = EXCLUDED.created_at;

SELECT setval('matching.swipe_events_id_seq', (SELECT MAX(id) FROM matching.swipe_events));

\echo 'Chargement des inscriptions'
INSERT INTO registrations (
    id, event_id, attendee_email, attendee_name, status, check_in_token, qr_code_data
)
VALUES
    (
        9100,
        500,
        'alice.martin@example.com',
        'Alice Martin',
        'confirmed',
        'CHK-ALICE-500',
        'alice-500'
    ),
    (
        9101,
        500,
        'bruno.leroy@example.com',
        'Bruno Leroy',
        'checked_in',
        'CHK-BRUNO-500',
        'bruno-500'
    ),
    (
        9102,
        501,
        'claire.dupont@example.com',
        'Claire Dupont',
        'confirmed',
        'CHK-CLAIRE-501',
        'claire-501'
    )
ON CONFLICT (id) DO UPDATE SET
    attendee_email = EXCLUDED.attendee_email,
    attendee_name = EXCLUDED.attendee_name,
    status = EXCLUDED.status,
    check_in_token = EXCLUDED.check_in_token,
    qr_code_data = EXCLUDED.qr_code_data,
    updated_at = NOW();

\echo 'Seed terminé.'
