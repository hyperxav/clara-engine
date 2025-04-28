-- Create function to execute raw SQL
CREATE OR REPLACE FUNCTION exec_sql(sql text)
RETURNS json AS $$
DECLARE
    result json;
    forbidden_keywords text[] := ARRAY['DROP', 'TRUNCATE', 'DELETE', 'ALTER ROLE', 'CREATE ROLE', 'DROP ROLE'];
    keyword text;
BEGIN
    -- Basic input validation
    IF sql IS NULL OR length(trim(sql)) = 0 THEN
        RETURN json_build_object('success', false, 'error', 'SQL query cannot be empty');
    END IF;

    -- Check for forbidden operations
    FOREACH keyword IN ARRAY forbidden_keywords LOOP
        IF upper(sql) ~* ('\m' || keyword || '\M') THEN
            RETURN json_build_object(
                'success', false,
                'error', 'Operation not allowed: ' || keyword,
                'detail', 'FORBIDDEN_OPERATION'
            );
        END IF;
    END LOOP;

    EXECUTE sql;
    result := json_build_object('success', true);
    RETURN result;
EXCEPTION WHEN OTHERS THEN
    result := json_build_object(
        'success', false,
        'error', SQLERRM,
        'detail', SQLSTATE
    );
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION exec_sql TO authenticated; 