-- =====================================================
-- WORKSHOP QC2PLUS - BASE DE DONNÉES SIMPLIFIÉE
-- =====================================================
-- 3 tables simples : Étudiants → Inscriptions → Cours
-- =====================================================


--- =====================================================
-- WORKSHOP QC2PLUS - BASE DE DONNÉES SIMPLIFIÉE
-- =====================================================
-- 3 tables simples : Étudiants → Inscriptions → Cours
-- =====================================================

CREATE DATABASE qc2plus;
CREATE USER qc2plus WITH PASSWORD '@qc2plus|kheopsys2025';

GRANT CONNECT ON DATABASE qc2plus_workshop TO qc2plus;
GRANT CREATE ON DATABASE qc2plus_workshop TO qc2plus;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO qc2plus; 

-- REVIEW pour les droits 
-- README pour la docs
-- RELATIONSHIP TABLES → MERGE
-- Tester les level 2 logiques de data quality pour chaque models
-- Temporalité des droits 
-- Ajouter tests de saisonalité (temporelle) dans les modèles 
-- Package pypy
-- Cleaning code

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO qc2plus;

-- Donne accès aux séquences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO qc2plus;
GRANT USAGE, CREATE ON SCHEMA public TO qc2plus;


DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS students CASCADE;

-- =====================================================
-- TABLE 1 : STUDENTS (Étudiants)
-- =====================================================
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    birth_date DATE,
    age INTEGER,
    city VARCHAR(50),
    country VARCHAR(50) DEFAULT 'France',
    registration_date DATE,
    status VARCHAR(20), -- active, inactive, graduated
    total_spent NUMERIC(10,2) DEFAULT 0,
    nb_courses INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE 2 : COURSES (Cours)
-- =====================================================
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    category VARCHAR(50),    -- Math, Science, Language, IT
    level VARCHAR(20),       -- Beginner, Intermediate, Advanced
    price NUMERIC(10,2),
    duration_hours INTEGER,
    teacher_name VARCHAR(100),
    max_students INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLE 3 : ENROLLMENTS (Inscriptions)
-- =====================================================
CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INTEGER,             -- REFERENCES students(student_id),
    course_id INTEGER,              -- REFERENCES courses(course_id),
    enrollment_date DATE NOT NULL,
    completion_date DATE,
    grade NUMERIC(5,2),             -- Note sur 100
    status VARCHAR(20),             -- enrolled, completed, dropped
    payment_amount NUMERIC(10,2),
    payment_status VARCHAR(20),     -- paid, pending, refunded
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- DONNÉES : STUDENTS (20 étudiants corrects + 5 avec problèmes)
-- =====================================================

-- Étudiants CORRECTS
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Jean', 'Dupont', 'jean.dupont@email.com', '+33612345678', '2000-03-15', 25, 'Paris', 'France', '2023-01-10', 'active', 2450.00, 5),
('Marie', 'Martin', 'marie.martin@email.com', '+33623456789', '1999-07-22', 26, 'Lyon', 'France', '2023-01-15', 'active', 3200.00, 7),
('Pierre', 'Bernard', 'pierre.bernard@email.com', '+33634567890', '2001-11-08', 24, 'Marseille', 'France', '2023-02-01', 'active', 1850.00, 4),
('Sophie', 'Dubois', 'sophie.dubois@email.com', '+33645678901', '1998-05-18', 27, 'Toulouse', 'France', '2023-02-10', 'active', 2980.00, 6),
('Luc', 'Thomas', 'luc.thomas@email.com', '+33656789012', '2002-01-30', 23, 'Nice', 'France', '2023-02-15', 'active', 1420.00, 3),

('Emma', 'Robert', 'emma.robert@email.com', '+33667890123', '1997-09-25', 28, 'Nantes', 'France', '2023-03-01', 'active', 4100.00, 9),
('Lucas', 'Petit', 'lucas.petit@email.com', '+33678901234', '2000-12-12', 25, 'Strasbourg', 'France', '2023-03-05', 'active', 2650.00, 5),
('Chloé', 'Durand', 'chloe.durand@email.com', '+33689012345', '2001-04-07', 24, 'Montpellier', 'France', '2023-03-10', 'active', 1920.00, 4),
('Alexandre', 'Leroy', 'alexandre.leroy@email.com', '+33690123456', '1998-08-14', 27, 'Bordeaux', 'France', '2023-03-15', 'active', 3500.00, 8),
('Julie', 'Moreau', 'julie.moreau@email.com', '+33601234567', '2002-06-20', 23, 'Lille', 'France', '2023-04-01', 'active', 1680.00, 3),

('Thomas', 'Simon', 'thomas.simon@email.com', '+33612345679', '1999-10-05', 26, 'Rennes', 'France', '2023-04-05', 'active', 2340.00, 5),
('Sarah', 'Laurent', 'sarah.laurent@email.com', '+33623456780', '2000-02-28', 25, 'Reims', 'France', '2023-04-10', 'active', 1890.00, 4),
('Antoine', 'Lefebvre', 'antoine.lefebvre@email.com', '+33634567891', '2001-07-16', 24, 'Le Havre', 'France', '2023-04-15', 'active', 2150.00, 5),
('Léa', 'Roux', 'lea.roux@email.com', '+33645678902', '1998-11-23', 27, 'Saint-Étienne', 'France', '2023-05-01', 'active', 3780.00, 8),
('Nicolas', 'Fournier', 'nicolas.fournier@email.com', '+33656789013', '2002-03-09', 23, 'Toulon', 'France', '2023-05-05', 'active', 1120.00, 2),

('Camille', 'Girard', 'camille.girard@email.com', '+33667890124', '1997-12-31', 28, 'Grenoble', 'France', '2023-05-10', 'active', 4250.00, 9),
('Julien', 'Bonnet', 'julien.bonnet@email.com', '+33678901235', '2000-05-11', 25, 'Angers', 'France', '2023-05-15', 'active', 1990.00, 4),
('Laura', 'Lambert', 'laura.lambert@email.com', '+33689012346', '2001-09-19', 24, 'Dijon', 'France', '2023-06-01', 'active', 2420.00, 5),
('Maxime', 'Fontaine', 'maxime.fontaine@email.com', '+33690123457', '1999-01-27', 26, 'Nîmes', 'France', '2023-06-05', 'active', 3120.00, 7),
('Manon', 'Chevalier', 'manon.chevalier@email.com', '+33601234568', '2002-08-03', 23, 'Aix-en-Provence', 'France', '2023-06-10', 'active', 1560.00, 3);

-- Étudiants avec PROBLÈMES (pour tests Niveau 1)

-- Problème 1 : Email NULL
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Paul', 'Gauthier', NULL, '+33612340001', '2000-04-12', 25, 'Paris', 'France', '2023-07-01', 'active', 1850.00, 4);

-- Problème 2 : Email mal formaté (sans @)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Claire', 'Perrin', 'claire.perrin.email.com', '+33623450001', '1999-08-30', 26, 'Lyon', 'France', '2023-07-05', 'active', 2100.00, 5);

-- Problème 3 : Âge aberrant (trop vieux)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Hugo', 'Rousseau', 'hugo.rousseau@email.com', '+33634560001', '1920-12-15', 250, 'Marseille', 'France', '2023-07-10', 'active', 890.00, 2);

-- Problème 4 : Âge aberrant (trop jeune)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Inès', 'Vincent', 'ines.vincent@email.com', '+33645670001', '2020-06-08', 5, 'Toulouse', 'France', '2023-07-15', 'active', 450.00, 1);

-- Problème 5 : Incohérence total_spent vs nb_courses (beaucoup de cours mais peu de dépenses)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Nathan', 'Muller', 'nathan.muller@email.com', '+33656780001', '2002-02-20', 23, 'Nice', 'France', '2023-08-01', 'active', 250.00, 10);

-- =====================================================
-- DONNÉES : COURSES (15 cours)
-- =====================================================

INSERT INTO courses (course_name, course_code, category, level, price, duration_hours, teacher_name, max_students, status) VALUES
-- Mathématiques
('Mathématiques Niveau 1', 'MATH101', 'Math', 'Beginner', 350.00, 20, 'Prof. Martin Dubois', 30, 'active'),
('Mathématiques Niveau 2', 'MATH201', 'Math', 'Intermediate', 450.00, 25, 'Prof. Martin Dubois', 25, 'active'),
('Mathématiques Avancées', 'MATH301', 'Math', 'Advanced', 650.00, 30, 'Prof. Sophie Laurent', 20, 'active'),

-- Sciences
('Physique Générale', 'PHYS101', 'Science', 'Beginner', 350.00, 20, 'Prof. Claire Bernard', 30, 'active'),
('Chimie Organique', 'CHEM201', 'Science', 'Intermediate', 480.00, 25, 'Prof. Luc Thomas', 25, 'active'),

-- Langues
('Anglais Débutant', 'ENG101', 'Language', 'Beginner', 300.00, 20, 'Prof. Emma Watson', 35, 'active'),
('Anglais Intermédiaire', 'ENG201', 'Language', 'Intermediate', 380.00, 25, 'Prof. Emma Watson', 30, 'active'),
('Anglais Avancé', 'ENG301', 'Language', 'Advanced', 520.00, 30, 'Prof. John Smith', 25, 'active'),
('Espagnol Débutant', 'ESP101', 'Language', 'Beginner', 300.00, 20, 'Prof. Maria Garcia', 35, 'active'),

-- Informatique
('Python Débutant', 'PY101', 'IT', 'Beginner', 420.00, 25, 'Prof. Alexandre Leroy', 25, 'active'),
('Python Avancé', 'PY301', 'IT', 'Advanced', 650.00, 35, 'Prof. Alexandre Leroy', 20, 'active'),
('Data Science', 'DS301', 'IT', 'Advanced', 850.00, 40, 'Prof. Julie Moreau', 18, 'active'),
('Développement Web', 'WEB201', 'IT', 'Intermediate', 580.00, 30, 'Prof. Thomas Simon', 22, 'active'),

-- Cours avec problèmes
('Cours Gratuit Bizarre', 'FREE001', 'IT', 'Beginner', 0.00, 0, 'Prof. Inconnu', 1000, 'inactive'),
('Cours Brouillon', 'NULL001', 'Unknown', 'Beginner', -100.00, 10, NULL, 0, 'active');

-- =====================================================
-- DONNÉES : ENROLLMENTS (avec relations et corrélations)
-- =====================================================

-- RÈGLE DE CORRÉLATION ATTENDUE :
-- Plus un étudiant a de courses (nb_courses), plus il dépense (total_spent)
-- Moyenne : 450€ par cours

-- Jean Dupont (5 cours, 2450€) - Corrélation OK : 490€/cours
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(1, 1, '2023-01-15', '2023-02-20', 85.50, 'completed', 350.00, 'paid'),
(1, 4, '2023-02-01', '2023-03-05', 78.00, 'completed', 350.00, 'paid'),
(1, 6, '2023-03-01', '2023-04-10', 92.00, 'completed', 300.00, 'paid'),
(1, 10, '2023-04-15', '2023-05-20', 88.50, 'completed', 420.00, 'paid'),
(1, 13, '2023-06-01', NULL, NULL, 'enrolled', 580.00, 'paid');

-- Marie Martin (7 cours, 3200€) - Corrélation OK : 457€/cours
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(2, 2, '2023-01-20', '2023-03-10', 91.00, 'completed', 450.00, 'paid'),
(2, 3, '2023-02-15', '2023-04-05', 88.00, 'completed', 650.00, 'paid'),
(2, 7, '2023-03-10', '2023-05-01', 86.50, 'completed', 380.00, 'paid'),
(2, 8, '2023-04-05', NULL, NULL, 'enrolled', 520.00, 'paid'),
(2, 11, '2023-05-01', NULL, NULL, 'enrolled', 650.00, 'paid'),
(2, 12, '2023-06-10', NULL, NULL, 'enrolled', 850.00, 'pending'),
(2, 13, '2023-07-01', NULL, NULL, 'enrolled', 580.00, 'pending');

-- Pierre Bernard (4 cours, 1850€) - Corrélation OK : 462€/cours
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(3, 1, '2023-02-05', '2023-03-15', 72.50, 'completed', 350.00, 'paid'),
(3, 6, '2023-02-20', '2023-04-01', 79.00, 'completed', 300.00, 'paid'),
(3, 9, '2023-04-10', '2023-05-20', 82.00, 'completed', 300.00, 'paid'),
(3, 10, '2023-05-25', NULL, NULL, 'enrolled', 420.00, 'paid');

-- Emma Robert (9 cours, 4100€) - Corrélation OK : 455€/cours
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(6, 3, '2023-03-05', '2023-05-15', 95.00, 'completed', 650.00, 'paid'),
(6, 5, '2023-03-10', '2023-05-01', 89.00, 'completed', 480.00, 'paid'),
(6, 8, '2023-04-01', '2023-06-10', 91.50, 'completed', 520.00, 'paid'),
(6, 11, '2023-05-05', NULL, NULL, 'enrolled', 650.00, 'paid'),
(6, 12, '2023-06-01', NULL, NULL, 'enrolled', 850.00, 'paid'),
(6, 13, '2023-07-01', NULL, NULL, 'enrolled', 580.00, 'paid'),
(6, 2, '2023-04-20', '2023-06-25', 87.00, 'completed', 450.00, 'paid'),
(6, 7, '2023-05-15', NULL, NULL, 'enrolled', 380.00, 'paid'),
(6, 4, '2023-03-20', '2023-05-10', 84.50, 'completed', 350.00, 'paid');

-- Inscriptions pour autres étudiants (corrélation normale)
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
-- Sophie Dubois (6 cours)
(4, 2, '2023-02-15', '2023-04-10', 86.00, 'completed', 450.00, 'paid'),
(4, 7, '2023-03-01', '2023-05-05', 83.50, 'completed', 380.00, 'paid'),
(4, 10, '2023-04-10', '2023-05-25', 88.00, 'completed', 420.00, 'paid'),
(4, 11, '2023-05-20', NULL, NULL, 'enrolled', 650.00, 'paid'),
(4, 13, '2023-06-15', NULL, NULL, 'enrolled', 580.00, 'paid'),
(4, 5, '2023-03-20', '2023-05-15', 81.00, 'completed', 480.00, 'paid'),

-- Luc Thomas (3 cours)
(5, 1, '2023-02-20', '2023-04-01', 75.00, 'completed', 350.00, 'paid'),
(5, 6, '2023-03-10', '2023-05-10', 77.50, 'completed', 300.00, 'paid'),
(5, 9, '2023-05-01', NULL, NULL, 'enrolled', 300.00, 'paid'),

-- Alexandre Leroy (8 cours)
(9, 3, '2023-03-20', '2023-06-01', 92.00, 'completed', 650.00, 'paid'),
(9, 5, '2023-03-25', '2023-05-20', 87.50, 'completed', 480.00, 'paid'),
(9, 8, '2023-04-10', '2023-06-20', 89.00, 'completed', 520.00, 'paid'),
(9, 11, '2023-05-15', NULL, NULL, 'enrolled', 650.00, 'paid'),
(9, 12, '2023-06-05', NULL, NULL, 'enrolled', 850.00, 'paid'),
(9, 13, '2023-07-10', NULL, NULL, 'enrolled', 580.00, 'paid'),
(9, 2, '2023-04-01', '2023-06-05', 85.00, 'completed', 450.00, 'paid'),
(9, 7, '2023-05-01', NULL, NULL, 'enrolled', 380.00, 'pending');

-- PROBLÈMES POUR TESTS NIVEAU 2

-- Problème : Corrélation rompue (Nathan Muller : 10 cours mais seulement 250€)
-- Attendu : ~4500€, Réel : 250€ → ANOMALIE !
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(25, 1, '2023-08-05', NULL, NULL, 'enrolled', 25.00, 'paid'),
(25, 2, '2023-08-06', NULL, NULL, 'enrolled', 25.00, 'paid'),
(25, 4, '2023-08-07', NULL, NULL, 'enrolled', 25.00, 'paid'),
(25, 6, '2023-08-08', NULL, NULL, 'enrolled', 25.00, 'paid'),
(25, 7, '2023-08-09', NULL, NULL, 'enrolled', 25.00, 'paid'),
(25, 9, '2023-08-10', NULL, NULL, 'enrolled', 25.00, 'paid'),
(25, 10, '2023-08-11', NULL, NULL, 'enrolled', 25.00, 'paid'),
(25, 5, '2023-08-12', NULL, NULL, 'enrolled', 25.00, 'paid'),
(25, 13, '2023-08-13', NULL, NULL, 'enrolled', 25.00, 'paid'),
(25, 8, '2023-08-14', NULL, NULL, 'enrolled', 25.00, 'paid');

-- Problème : Grade aberrant (négatif)
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(10, 1, '2023-04-05', '2023-06-01', -25.00, 'completed', 350.00, 'paid');

-- Problème : Grade aberrant (> 100)
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(12, 2, '2023-04-10', '2023-06-10', 150.00, 'completed', 450.00, 'paid');

-- Problème : Foreign key invalide (cours inexistant)
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(15, 999, '2023-05-01', NULL, NULL, 'enrolled', 500.00, 'paid');

-- Problème : Dates incohérentes (completion avant enrollment)
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(18, 3, '2023-06-15', '2023-05-01', 80.00, 'completed', 650.00, 'paid');


-- =====================================================
-- RÉSUMÉ DES PROBLÈMES POUR LE WORKSHOP
-- =====================================================

/*
PROBLÈMES NIVEAU 1 (Tests déterministes) :
1. Email NULL : student_id = 21 (Paul Gauthier)
2. Email mal formaté : student_id = 22 (Claire Perrin)
3. Âge > 100 : student_id = 23 (Hugo Rousseau, 250 ans)
4. Âge < 16 : student_id = 24 (Inès Vincent, 5 ans)
5. Grade négatif : enrollment avec student_id = 10
6. Grade > 100 : enrollment avec student_id = 12
7. Foreign key invalide : enrollment avec course_id = 999
8. Dates incohérentes : enrollment avec student_id = 18

PROBLÈMES NIVEAU 2 (Anomalies ML/IA) :
1. Corrélation rompue : student_id = 25 (Nathan Muller)
   - 10 cours mais seulement 250€ au lieu de ~4500€
   - Cette anomalie sera détectée par l'analyse de corrélation

STATISTIQUES ATTENDUES :
- 25 étudiants au total
- 20 étudiants corrects
- 5 étudiants avec problèmes Niveau 1
- 1 étudiant avec problème Niveau 2 (corrélation)
- 15 cours disponibles
- Corrélation attendue : ~450€ par cours en moyenne
*/

SELECT 'Base de données workshop créée avec succès !' as message,
       (SELECT COUNT(*) FROM students) as nb_students,
       (SELECT COUNT(*) FROM courses) as nb_courses,
       (SELECT COUNT(*) FROM enrollments) as nb_enrollments;