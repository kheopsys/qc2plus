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

-- FRANCE (15 étudiants - préférence Math + IT)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Jean', 'Dupont', 'jean.dupont@email.com', '+33612345678', '2000-03-15', 25, 'Paris', 'France', '2025-09-10', 'active', 2100.00, 5),
('Marie', 'Martin', 'marie.martin@email.com', '+33623456789', '1999-07-22', 26, 'Paris', 'France', '2025-09-15', 'active', 2800.00, 6),
('Pierre', 'Bernard', 'pierre.bernard@email.com', '+33634567890', '2001-11-08', 24, 'Lyon', 'France', '2025-10-01', 'active', 1350.00, 3),
('Sophie', 'Dubois', 'sophie.dubois@email.com', '+33645678901', '1998-05-18', 27, 'Lyon', 'France', '2025-10-10', 'active', 2250.00, 5),
('Luc', 'Thomas', 'luc.thomas@email.com', '+33656789012', '2002-01-30', 23, 'Marseille', 'France', '2025-10-15', 'active', 900.00, 2),
('Emma', 'Robert', 'emma.robert@email.com', '+33667890123', '1997-09-25', 28, 'Paris', 'France', '2025-11-01', 'active', 3150.00, 7),
('Lucas', 'Petit', 'lucas.petit@email.com', '+33678901234', '2000-12-12', 25, 'Toulouse', 'France', '2025-11-05', 'active', 1800.00, 4),
('Chloé', 'Durand', 'chloe.durand@email.com', '+33689012345', '2001-04-07', 24, 'Nice', 'France', '2025-11-10', 'active', 1350.00, 3),
('Alexandre', 'Leroy', 'alexandre.leroy@email.com', '+33690123456', '1998-08-14', 27, 'Bordeaux', 'France', '2025-11-15', 'active', 2700.00, 6),
('Julie', 'Moreau', 'julie.moreau@email.com', '+33601234567', '2002-06-20', 23, 'Lille', 'France', '2025-12-01', 'active', 900.00, 2),
('Thomas', 'Simon', 'thomas.simon@email.com', '+33612345679', '1999-10-05', 26, 'Nantes', 'France', '2025-12-05', 'active', 1800.00, 4),
('Sarah', 'Laurent', 'sarah.laurent@email.com', '+33623456780', '2000-02-28', 25, 'Strasbourg', 'France', '2025-12-10', 'active', 1350.00, 3),
('Antoine', 'Lefebvre', 'antoine.lefebvre@email.com', '+33634567891', '2001-07-16', 24, 'Rennes', 'France', '2025-09-01', 'active', 1800.00, 4),
('Léa', 'Roux', 'lea.roux@email.com', '+33645678902', '1998-11-23', 27, 'Grenoble', 'France', '2025-09-05', 'active', 2700.00, 6),
('Nicolas', 'Fournier', 'nicolas.fournier@email.com', '+33656789013', '2002-03-09', 23, 'Montpellier', 'France', '2025-10-01', 'active', 900.00, 2);

-- BELGIQUE (5 étudiants - forte préférence Language)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Liam', 'Dupont', 'liam.dupont@email.be', '+3224567890', '2000-01-10', 25, 'Brussels', 'Belgium', '2025-09-18', 'active', 1120.00, 4),
('Olivia', 'Peeters', 'olivia.peeters@email.be', '+3235678901', '1999-06-22', 26, 'Brussels', 'Belgium', '2025-10-03', 'active', 1620.00, 5),
('Noah', 'Janssens', 'noah.janssens@email.be', '+3246789012', '2001-09-14', 24, 'Antwerp', 'Belgium', '2025-10-19', 'active', 1320.00, 4),
('Emma', 'Maes', 'emma.maes@email.be', '+3257890123', '1998-12-05', 27, 'Ghent', 'Belgium', '2025-11-07', 'active', 1920.00, 6),
('Louis', 'Claes', 'louis.claes@email.be', '+3279012345', '2000-11-12', 25, 'Bruges', 'Belgium', '2025-12-11', 'active', 820.00, 3);

-- SUISSE (5 étudiants - forte préférence IT + Math)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Lukas', 'Müller', 'lukas.mueller@email.ch', '+41445678901', '2000-02-18', 25, 'Zurich', 'Switzerland', '2025-09-22', 'active', 2700.00, 6),
('Anna', 'Schneider', 'anna.schneider@email.ch', '+41556789012', '1999-07-31', 26, 'Zurich', 'Switzerland', '2025-10-09', 'active', 3150.00, 7),
('David', 'Fischer', 'david.fischer@email.ch', '+41667890123', '2001-10-14', 24, 'Geneva', 'Switzerland', '2025-10-26', 'active', 2250.00, 5),
('Laura', 'Weber', 'laura.weber@email.ch', '+41778901234', '1998-05-27', 27, 'Basel', 'Switzerland', '2025-11-16', 'active', 2700.00, 6),
('Marc', 'Meyer', 'marc.meyer@email.ch', '+41889012345', '2002-08-09', 23, 'Lausanne', 'Switzerland', '2025-12-03', 'active', 1800.00, 4);

-- Étudiants avec PROBLÈMES (pour tests Niveau 1)

-- Problème 1 : Email NULL
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Paul', 'Gauthier', NULL, '+33612340001', '2000-04-12', 25, 'Paris', 'France', '2025-10-15', 'active', 1350.00, 4);

-- Problème 2 : Email mal formaté (sans @)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Claire', 'Perrin', 'claire.perrin.email.com', '+33623450001', '1999-08-30', 26, 'Lyon', 'France', '2025-10-16', 'active', 1800.00, 5);

-- Problème 3 : Âge aberrant (trop vieux)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Hugo', 'Rousseau', 'hugo.rousseau@email.com', '+33634560001', '1920-12-15', 250, 'Marseille', 'France', '2025-10-17', 'active', 450.00, 2);

-- Problème 4 : Âge aberrant (trop jeune)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Inès', 'Vincent', 'ines.vincent@email.com', '+33645670001', '2020-06-08', 5, 'Toulouse', 'France', '2025-10-17', 'active', 300.00, 1);

-- Problème 5 : Incohérence total_spent vs nb_courses (beaucoup de cours mais peu de dépenses)
INSERT INTO students (first_name, last_name, email, phone, birth_date, age, city, country, registration_date, status, total_spent, nb_courses) VALUES
('Nathan', 'Muller', 'nathan.muller@email.com', '+33656780001', '2002-02-20', 23, 'Nice', 'France', '2025-10-19', 'active', 250.00, 10);

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
-- =====================================================
-- ENROLLMENTS AVEC PATTERNS TEMPORELS
-- =====================================================
-- Pattern sur 6 mois (Jan à Juin 2025)
-- Baseline = 10 inscriptions/mois
-- Janvier : Pic +50% = 15 inscriptions
-- Mars : ANOMALIE +100% = 20 inscriptions (IT)
-- Juin : ANOMALIE -80% = 2 inscriptions
-- =====================================================

-- JANVIER 2025 : Pic de rentrée (+50%)
-- 15 inscriptions
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
-- France - Math + IT
(1, 1, '2025-09-10', '2025-10-28', 85.50, 'completed', 350.00, 'paid'),
(1, 9, '2025-09-11', NULL, NULL, 'enrolled', 420.00, 'paid'),
(2, 2, '2025-09-15', '2025-11-10', 91.00, 'completed', 450.00, 'paid'),
(2, 10, '2025-09-16', NULL, NULL, 'enrolled', 650.00, 'paid'),
(3, 1, '2025-09-20', '2025-11-05', 78.50, 'completed', 350.00, 'paid'),

-- Belgique - Language
(16, 6, '2025-09-18', '2025-11-15', 82.00, 'completed', 300.00, 'paid'),
(16, 8, '2025-09-19', NULL, NULL, 'enrolled', 300.00, 'paid'),
(17, 6, '2025-09-24', '2025-11-20', 88.50, 'completed', 300.00, 'paid'),

-- Suisse - IT + Math
(21, 10, '2025-09-22', NULL, NULL, 'enrolled', 650.00, 'paid'),
(21, 2, '2025-09-23', '2025-12-05', 93.00, 'completed', 450.00, 'paid'),
(22, 11, '2025-09-25', NULL, NULL, 'enrolled', 850.00, 'paid'),
(22, 10, '2025-09-26', '2025-12-10', 89.50, 'completed', 650.00, 'paid'),

-- France additions
(4, 3, '2025-09-28', '2025-11-25', 84.00, 'completed', 480.00, 'paid'),
(5, 4, '2025-09-29', '2025-11-20', 79.00, 'completed', 350.00, 'paid'),
(6, 11, '2025-09-30', NULL, NULL, 'enrolled', 850.00, 'paid');

-- FÉVRIER 2025 : Baseline normal
-- 10 inscriptions
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(7, 1, '2025-10-05', '2025-12-01', 75.00, 'completed', 350.00, 'paid'),
(8, 9, '2025-10-08', NULL, NULL, 'enrolled', 420.00, 'paid'),
(9, 10, '2025-10-10', NULL, NULL, 'enrolled', 650.00, 'paid'),
(11, 1, '2025-10-12', '2025-12-05', 80.00, 'completed', 350.00, 'paid'),

(18, 7, '2025-10-14', '2025-12-10', 85.00, 'completed', 520.00, 'paid'),
(19, 6, '2025-10-16', '2025-12-12', 87.50, 'completed', 300.00, 'paid'),

(23, 2, '2025-10-18', '2025-09-01', 91.00, 'completed', 450.00, 'paid'),
(24, 10, '2025-10-20', NULL, NULL, 'enrolled', 650.00, 'paid'),

(4, 9, '2025-10-22', '2025-12-20', 83.00, 'completed', 420.00, 'paid'),
(6, 12, '2025-10-24', NULL, NULL, 'enrolled', 580.00, 'paid');

-- MARS 2025 : ANOMALIE - Pic inexpliqué (+100%) + Concentration IT
-- 20 inscriptions (au lieu de 10) - 16 en IT !
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
-- Explosion IT
(1, 11, '2025-11-01', NULL, NULL, 'enrolled', 850.00, 'paid'),
(2, 12, '2025-11-02', NULL, NULL, 'enrolled', 580.00, 'paid'),
(7, 10, '2025-11-03', NULL, NULL, 'enrolled', 650.00, 'paid'),
(8, 11, '2025-11-04', NULL, NULL, 'enrolled', 850.00, 'paid'),
(9, 12, '2025-11-05', NULL, NULL, 'enrolled', 580.00, 'paid'),
(11, 10, '2025-11-06', NULL, NULL, 'enrolled', 650.00, 'paid'),
(12, 11, '2025-11-07', NULL, NULL, 'enrolled', 850.00, 'paid'),
(13, 9, '2025-11-08', NULL, NULL, 'enrolled', 420.00, 'paid'),
(14, 10, '2025-11-09', NULL, NULL, 'enrolled', 650.00, 'paid'),
(3, 10, '2025-11-10', NULL, NULL, 'enrolled', 650.00, 'paid'),

-- Belgique IT aussi
(17, 9, '2025-11-11', NULL, NULL, 'enrolled', 420.00, 'paid'),
(18, 10, '2025-11-12', NULL, NULL, 'enrolled', 650.00, 'paid'),

-- Suisse IT
(23, 11, '2025-11-13', NULL, NULL, 'enrolled', 850.00, 'paid'),
(24, 12, '2025-11-14', NULL, NULL, 'enrolled', 580.00, 'paid'),
(25, 10, '2025-11-15', NULL, NULL, 'enrolled', 650.00, 'paid'),

-- Quelques non-IT
(4, 6, '2025-11-16', NULL, NULL, 'enrolled', 300.00, 'paid'),
(5, 7, '2025-11-17', NULL, NULL, 'enrolled', 520.00, 'paid'),
(21, 3, '2025-11-18', NULL, NULL, 'enrolled', 480.00, 'paid'),
(22, 2, '2025-11-19', NULL, NULL, 'enrolled', 450.00, 'paid'),
(6, 2, '2025-11-20', NULL, NULL, 'enrolled', 450.00, 'paid');

-- AVRIL 2025 : Retour baseline
-- 10 inscriptions
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(13, 2, '2025-12-02', '2025-10-10', 84.00, 'completed', 450.00, 'paid'),
(14, 3, '2025-12-04', '2025-10-12', 87.50, 'completed', 480.00, 'paid'),
(15, 1, '2025-12-06', '2025-10-15', 82.00, 'completed', 350.00, 'paid'),
(1, 12, '2025-12-08', NULL, NULL, 'enrolled', 580.00, 'paid'),

(19, 7, '2025-12-10', '2025-10-20', 88.00, 'completed', 520.00, 'paid'),
(20, 6, '2025-12-12', '2025-10-22', 86.50, 'completed', 300.00, 'paid'),

(23, 3, '2025-12-14', '2025-11-01', 92.00, 'completed', 480.00, 'paid'),
(24, 9, '2025-12-16', NULL, NULL, 'enrolled', 420.00, 'paid'),

(5, 6, '2025-12-18', '2025-10-25', 83.50, 'completed', 300.00, 'paid'),
(7, 2, '2025-12-20', '2025-10-28', 85.00, 'completed', 450.00, 'paid');

-- MAI 2025 : Baseline
-- 10 inscriptions
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(2, 3, '2025-09-02', NULL, NULL, 'enrolled', 480.00, 'paid'),
(3, 9, '2025-09-04', NULL, NULL, 'enrolled', 420.00, 'paid'),
(4, 10, '2025-09-06', NULL, NULL, 'enrolled', 650.00, 'paid'),
(8, 2, '2025-09-08', '2025-11-18', 88.50, 'completed', 450.00, 'paid'),

(16, 7, '2025-09-10', '2025-11-20', 87.00, 'completed', 520.00, 'paid'),
(17, 8, '2025-09-12', '2025-11-22', 85.50, 'completed', 300.00, 'paid'),

(21, 12, '2025-09-14', NULL, NULL, 'enrolled', 580.00, 'paid'),
(22, 11, '2025-09-16', NULL, NULL, 'enrolled', 850.00, 'paid'),

(9, 2, '2025-09-18', NULL, NULL, 'enrolled', 450.00, 'paid'),
(10, 1, '2025-09-20', '2025-11-25', 84.00, 'completed', 350.00, 'paid');

-- JUIN 2025 : ANOMALIE - Chute brutale (-80%)
-- 2 inscriptions (au lieu de 10)
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(12, 1, '2025-10-05', '2025-12-10', 76.00, 'completed', 350.00, 'paid'),
(25, 3, '2025-10-15', '2025-12-15', 82.50, 'completed', 480.00, 'paid');

-- =====================================================
-- ENROLLMENTS POUR ÉTUDIANT AVEC PROBLÈME CORRÉLATION
-- =====================================================
-- Student 30 (Nathan Anomalie) : 8 cours mais seulement 200€
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(30, 1, '2025-10-20', NULL, NULL, 'enrolled', 25.00, 'paid'),
(30, 2, '2025-10-21', NULL, NULL, 'enrolled', 25.00, 'paid'),
(30, 4, '2025-10-22', NULL, NULL, 'enrolled', 25.00, 'paid'),
(30, 6, '2025-10-23', NULL, NULL, 'enrolled', 25.00, 'paid'),
(30, 7, '2025-10-24', NULL, NULL, 'enrolled', 25.00, 'paid'),
(30, 9, '2025-10-25', NULL, NULL, 'enrolled', 25.00, 'paid'),
(30, 10, '2025-10-26', NULL, NULL, 'enrolled', 25.00, 'paid'),
(30, 5, '2025-10-27', NULL, NULL, 'enrolled', 25.00, 'paid');

-- =====================================================
-- ENROLLMENTS AVEC PROBLÈMES NIVEAU 1
-- =====================================================

-- Problème : Grade négatif
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(10, 2, '2025-12-05', '2025-10-01', -25.00, 'completed', 450.00, 'paid');

-- Problème : Grade > 100
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(12, 3, '2025-12-10', '2025-10-10', 150.00, 'completed', 480.00, 'paid');

-- Problème : Dates incohérentes (completion avant enrollment)
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(15, 4, '2025-10-15', '2025-09-01', 80.00, 'completed', 350.00, 'paid');

-- Problème : Foreign key invalide (cours inexistant)
INSERT INTO enrollments (student_id, course_id, enrollment_date, completion_date, grade, status, payment_amount, payment_status) VALUES
(18, 999, '2025-09-01', NULL, NULL, 'enrolled', 500.00, 'paid');


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

*/

SELECT 'Base de données workshop créée avec succès !' as message,
       (SELECT COUNT(*) FROM students) as nb_students,
       (SELECT COUNT(*) FROM courses) as nb_courses,
       (SELECT COUNT(*) FROM enrollments) as nb_enrollments;