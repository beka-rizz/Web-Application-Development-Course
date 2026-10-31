DROP DATABASE IF EXISTS bounty_hunters;
CREATE DATABASE bounty_hunters CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bounty_hunters;

CREATE TABLE wanted_criminals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NULL,
    nickname VARCHAR(255) NOT NULL,
    reward DECIMAL(12, 2) NOT NULL,
    latitude DECIMAL(9, 6) NULL,
    longitude DECIMAL(9, 6) NULL,
    location_note VARCHAR(500) NULL,
    difficulty TINYINT NOT NULL,
    armed BOOLEAN NOT NULL,
    has_crew BOOLEAN NOT NULL,
    escape_master BOOLEAN NOT NULL,
    CONSTRAINT chk_difficulty CHECK (difficulty BETWEEN 1 AND 10),
    CONSTRAINT chk_reward CHECK (reward >= 0),
    CONSTRAINT chk_coords_pair CHECK (
        (latitude IS NULL AND longitude IS NULL)
        OR (latitude IS NOT NULL AND longitude IS NOT NULL)
    ),
    CONSTRAINT chk_latitude CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_longitude CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
    CONSTRAINT chk_location_present CHECK (
        location_note IS NOT NULL
        OR (latitude IS NOT NULL AND longitude IS NOT NULL)
    )
);

CREATE TABLE hunt_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    criminal_id INT NOT NULL,
    success BOOLEAN NOT NULL,
    notes TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hunt_criminal FOREIGN KEY (criminal_id) REFERENCES wanted_criminals (id)
);

INSERT INTO wanted_criminals
    (name, nickname, reward, latitude, longitude, location_note, difficulty, armed, has_crew, escape_master)
VALUES
    ('Kael Voss', 'Red Comet', 15000.00, 41.008200, 28.978400, NULL, 7, 1, 1, 1),
    (NULL, 'Silent Orbit', 4200.00, NULL, NULL, 'Drifted past the Titan relay, heading spinward', 4, 0, 0, 1),
    ('Mira Chen', 'Glass Widow', 25000.00, -33.868800, 151.209300, NULL, 9, 1, 0, 1),
    ('Torin Hale', 'Dust Baron', 8000.00, 48.856600, 2.352200, 'Spotted in the dry docks', 6, 1, 1, 0),
    ('Lina Ortega', 'Pale Signal', 2500.00, NULL, NULL, 'Only a scrambled beacon remains near Ceres', 3, 0, 0, 0);

INSERT INTO hunt_logs (criminal_id, success, notes, created_at) VALUES
    (1, 0, 'Target broke contact after a short pursuit.', '2026-01-12 09:15:00'),
    (1, 1, 'Captured at the orbital dry dock.', '2026-02-03 18:40:00'),
    (2, 0, 'Target escaped through an asteroid field.', '2026-01-20 11:05:00'),
    (2, 0, 'Beacon went dark near the Titan relay.', '2026-03-01 07:25:00'),
    (3, 0, 'Sniper fire from the ridge. Pulled back.', '2026-01-28 22:10:00'),
    (3, 1, 'Stunned and secured aboard the hunter ship.', '2026-04-14 16:55:00'),
    (4, 0, 'Crew laid down cover. Suspect fled on a skiff.', '2026-02-17 13:30:00'),
    (4, 1, 'Cornered in the cargo maze and cuffed.', '2026-05-02 19:05:00'),
    (5, 0, 'Only found a discarded transmitter.', '2026-03-09 08:45:00'),
    (5, 0, 'Ambush missed. No visual on the suspect.', '2026-06-21 21:15:00');
