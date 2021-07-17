-- Création des tables

CREATE TABLE users (
	user_tag VARCHAR(25) PRIMARY KEY NOT NULL,
	user_name VARCHAR(100) NOT NULL,
	user_picture VARCHAR(100) NOT NULL,
	user_mail VARCHAR(255) NOT NULL,
	user_password VARCHAR(255) NOT NULL,
	user_creation_date DATE NOT NULL,
	UNIQUE KEY unique_email (user_mail),
	UNIQUE KEY unique_tag (user_tag)
);

CREATE TABLE shows (
	show_tag INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
	show_id INT NOT NULL,
	show_type VARCHAR(5) NOT NULL CHECK (show_type IN ('SERIE', 'MOVIE')),
	show_name VARCHAR(100) NOT NULL
);

CREATE TABLE liked (
	user_tag VARCHAR(25),
	show_tag INT,
	CONSTRAINT fk_users FOREIGN KEY (user_tag) REFERENCES users(user_tag) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT fk_shows FOREIGN KEY (show_tag) REFERENCES shows(show_tag) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Trigger pour créer une pair unique (user_tag, show_tag)

DELIMITER $$
CREATE TRIGGER unique_liked_show BEFORE INSERT ON liked
FOR EACH ROW
BEGIN
	IF EXISTS (SELECT * FROM liked WHERE user_tag = new.user_tag AND show_tag = new.show_tag)
	THEN
    	SIGNAL sqlstate '45000' SET message_text = 'The serie/movie has already been liked';
	END IF;
END $$
DELIMITER ;

-- Fonction pour détecter si le nom d’utilisateur et le mail sont uniques

DELIMITER $$
CREATE FUNCTION is_unique(tag VARCHAR(25), mail VARCHAR(255)) RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
	DECLARE isIn BOOLEAN DEFAULT 0;
	DECLARE total INT;
	SET total = (SELECT COUNT(*) FROM users WHERE user_mail = mail OR user_tag = tag);
	IF total = 0 THEN SET isIn = 1;
	END IF;
	RETURN isIn;
END $$
DELIMITER ;

-- Fonction pour détecter si un show a déjà été aimé par un utilisateur

DELIMITER $$
CREATE FUNCTION is_liked(tag VARCHAR(25), id INTEGER) RETURNS BOOLEAN
READS SQL DATA
DETERMINISTIC
BEGIN
	DECLARE isIn BOOLEAN DEFAULT 0;
	DECLARE req INT;
	SET req = (SELECT show_tag FROM liked WHERE user_tag = tag and show_tag = id);
	IF req IS NOT NULL THEN SET isIn = 1;
	END IF;
	RETURN isIn;
END $$
DELIMITER ;
