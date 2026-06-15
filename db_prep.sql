DROP MATERIALIZED VIEW filtered;
DROP MATERIALIZED VIEW has_required_tags;

SET work_mem = '512MB';

CREATE MATERIALIZED VIEW IF NOT EXISTS image_taggings_named AS (
	SELECT it.image_id, t.name FROM image_taggings it JOIN tags t
		ON it.tag_id = t.id
);

CREATE MATERIALIZED VIEW IF NOT EXISTS candidates AS (
	SELECT image_id FROM image_taggings_named itn
		WHERE name IN ('safe', 'solo', 'pony')
		AND NOT EXISTS (
			SELECT 1 FROM image_hides h
			WHERE h.image_id = itn.image_id
		)
		AND NOT EXISTS (
			SELECT 1 FROM image_duplicates d
			WHERE d.image_id = itn.image_id
		)
		GROUP BY image_id
		HAVING COUNT(DISTINCT name) = 3
		EXCEPT
		SELECT image_id FROM image_taggings_named
			WHERE name IN ('portrait', 'close-up', 'head only', 'icon', 'animated')
);

CREATE MATERIALIZED VIEW IF NOT EXISTS filtered AS
SELECT id, created_at, image_format
	FROM images i JOIN candidates c
		ON i.id = c.image_id
	WHERE score >= 80
		AND image_format IN ('png', 'jpg') -- svg later
		AND image_aspect_ratio BETWEEN 0.5 AND 2
		AND image_size <= 15000000
ORDER BY created_at ASC;

SELECT COUNT(*) FROM filtered;

SELECT t.name, o.occurences
FROM (
	SELECT tag_id, COUNT(*) occurences FROM image_taggings
	WHERE image_id IN (SELECT id FROM filtered)
	GROUP BY tag_id
) AS o JOIN tags t ON t.id = o.tag_id
WHERE t.name NOT LIKE 'artist:%'
ORDER BY occurences DESC
LIMIT 500;


CREATE OR REPLACE FUNCTION get_image_data (IN img_ids INT[])
RETURNS TABLE (
	id INT,
	created_at TIMESTAMP,
	image_format TEXT,
	score INT,
	tags TEXT[]
)
LANGUAGE sql
STABLE
AS $$
	WITH RECURSIVE ids(id) AS (
		SELECT unnest(img_ids)
	), taggings AS (
		SELECT image_id, tag_id
			FROM image_taggings it JOIN ids
				ON it.image_id = ids.id
		UNION
		SELECT image_id, ti.target_tag_id AS tag_id
			FROM taggings t JOIN tag_implications ti
			ON t.tag_id = ti.tag_id
	)
	SELECT ids.id, i.created_at, i.image_format, i.score, array_agg(tags.name) tags
		FROM ids JOIN taggings t
			ON t.image_id = ids.id
		JOIN tags
			ON tags.id = t.tag_id
		JOIN images i
			ON i.id = ids.id
		GROUP BY ids.id, i.created_at, i.score, i.image_format;
$$;
