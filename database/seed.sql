USE smart_timetable_db;

INSERT INTO users (name, username, email, password, role)
VALUES
('Admin User', 'admin', 'admin@gmail.com', 'admin123', 'admin'),
('HOD User', 'hod', 'hod@gmail.com', 'hod123', 'hod'),
('Teacher User', 'teacher', 'teacher@gmail.com', 'teacher123', 'teacher');

INSERT INTO teachers (user_id, designation, department_name)
VALUES
(3, 'Lecturer', 'Computer Science');

INSERT INTO rooms (room_name, room_type)
VALUES
('Classroom 1', 'classroom'),
('Classroom 2', 'classroom'),
('Classroom 3', 'classroom'),
('Classroom 4', 'classroom'),
('Lab Room 1', 'lab');