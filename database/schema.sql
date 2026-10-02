CREATE TABLE juegos ( 
    id INTEGER PRIMARY KEY, 
    titulo TEXT NOT NULL CHECK (TRIM(titulo) != ''), 
    plataforma TEXT NOT NULL CHECK (plataforma IN ('PC', 'PlayStation', 'Xbox', 'Switch')), 
    tienda TEXT CHECK ( 
        ( 
            plataforma = 'PC' 
            AND tienda IS NOT NULL 
            AND tienda IN ('Steam', 'Epic Games', 'GOG') 
        ) 
        OR 
        ( 
            plataforma != 'PC' 
            AND tienda IS NULL 
        ) 
    ), 
    estado TEXT NOT NULL CHECK (
        estado in ('sin jugar', 'jugando', 'abandonado', 'terminado') 
)
);

CREATE UNIQUE INDEX control_PC 
ON juegos (titulo, plataforma, tienda) 
WHERE plataforma = 'PC';

CREATE UNIQUE INDEX control_consola 
ON juegos (titulo, plataforma) 
WHERE plataforma != 'PC';