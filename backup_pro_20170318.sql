-- MySQL dump 10.13  Distrib 5.7.16, for Win64 (x86_64)
--
-- Host: localhost    Database: monitor
-- ------------------------------------------------------
-- Server version	5.7.16-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping routines for database 'monitor'
--
/*!50003 DROP PROCEDURE IF EXISTS `record_backup` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `record_backup`()
BEGIN
		/*
			表domain_result数据每5分钟拷贝至表domain_responsestatus,表domain_responsetime
		*/			
		DECLARE  interval_time int default 2;
    DECLARE  _done int default 0;
		DECLARE  domain_id int;

		DECLARE  slowest_ip_id int;
		DECLARE  fastest_ip_id int;
		DECLARE  slowest_time VARCHAR(10);
		DECLARE  fastest_time VARCHAR(10);
		DECLARE  slowest_size VARCHAR(15);
		DECLARE  fastest_size VARCHAR(15);
		DECLARE  slowest_speed VARCHAR(15);
		DECLARE  fastest_speed VARCHAR(15);
		DECLARE  slowest_redirect VARCHAR(2);
		DECLARE  fastest_redirect VARCHAR(2);

		DECLARE  create_time DATETIME;
		#开始恢复时间
		DECLARE  start_time DATETIME DEFAULT '2016-12-14 10:44:33';
		#结束恢复时间
		DECLARE  end_time DATETIME DEFAULT '2016-12-14 17:50:35';
		#当前时间
		DECLARE  cur_time DATETIME;
		#临时时间
		DECLARE  temp_time DATETIME;
		
		DECLARE  response_status VARCHAR(5);
		DECLARE  proxy_id int;

		DECLARE _cur CURSOR FOR SELECT id FROM domain_domain;

		DECLARE CONTINUE HANDLER FOR 1329 SET _done = 1;#错误定义，标记循环结束 
		/* 打开光标 */  
    OPEN _Cur; 
		REPEAT  
				FETCH _Cur INTO domain_id;
				IF NOT _done THEN					
					set cur_time=end_time;
					WHILE cur_time>start_time DO
						set temp_time=cur_time - INTERVAL interval_time MINUTE;
						#最快
						SELECT r.total_time,r.ipaddr_id,r.size_download,r.speed_download,r.redirect_count INTO fastest_time,fastest_ip_id,fastest_size,fastest_speed,fastest_redirect FROM domain_result r,domain_domain d where r.domain_id=d.id and r.create_time<=cur_time and r.create_time>temp_time and d.id=domain_id and r.total_time>0 order by r.total_time LIMIT 1;
						#最慢
						SELECT r.total_time,r.ipaddr_id,r.create_time,r.size_download,r.speed_download,r.redirect_count INTO slowest_time,slowest_ip_id,create_time,slowest_size,slowest_speed,slowest_redirect FROM domain_result r,domain_domain d where r.domain_id=d.id and r.create_time<=cur_time and r.create_time>temp_time and d.id=domain_id order by r.total_time DESC LIMIT 1;											
						IF NOT slowest_time IS NULL and NOT fastest_time IS NULL THEN
							#插入状态表
							INSERT INTO domain_responsestatus (ipaddr_id,proxy_id,domain_id,http_code,total_time,create_time,status) SELECT a.ipaddr_id,a.proxy_id,a.domain_id,a.http_code,a.total_time,a.create_time,a.status FROM domain_result as a where a.domain_id=domain_id and a.create_time<=cur_time and a.create_time>temp_time;							
							#插入最快最慢表
							INSERT INTO domain_responsetime (slowest_ip_id,fastest_ip_id,slowest_time,fastest_time,domain_id,create_time,status,fastest_size,fastest_speed,fastest_redirect,slowest_size,slowest_speed,slowest_redirect) VALUES (slowest_ip_id,fastest_ip_id,slowest_time,fastest_time,domain_id,create_time,1,fastest_size,fastest_speed,fastest_redirect,slowest_size,slowest_speed,slowest_redirect);						
							#top
							#select _done,temp_time;
						END IF;
						set cur_time= temp_time;
					END WHILE;
					set _done=1;
				END IF;  
    UNTIL _done END REPEAT; #当_done=1时退出被循 
		/*关闭光标*/  
    CLOSE _Cur;  
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 DROP PROCEDURE IF EXISTS `record_domain_sort_out` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `record_domain_sort_out`()
BEGIN
		/*
			表domain_result数据每5分钟拷贝至表domain_responsestatus,表domain_responsetime
		*/			
		DECLARE  interval_time int default 2;
    DECLARE  _done int default 0;
		DECLARE  domain_id int;

		DECLARE  slowest_ip_id int;
		DECLARE  fastest_ip_id int;
		DECLARE  slowest_time VARCHAR(10);
		DECLARE  fastest_time VARCHAR(10);
		DECLARE  slowest_size VARCHAR(15);
		DECLARE  fastest_size VARCHAR(15);
		DECLARE  slowest_speed VARCHAR(15);
		DECLARE  fastest_speed VARCHAR(15);
		DECLARE  slowest_redirect VARCHAR(2);
		DECLARE  fastest_redirect VARCHAR(2);
		DECLARE  log_info VARCHAR(500) DEFAULT '';

		DECLARE  create_time DATETIME;
		DECLARE  response_status VARCHAR(5);
		DECLARE  proxy_id int;
		
		DECLARE _Cur CURSOR FOR
		SELECT id FROM domain_domain;
		
		DECLARE CONTINUE HANDLER FOR 1329 SET _done = 1;#错误定义，标记循环结束  
		insert into domain_log (log) SELECT concat('start time:',now());
		/* 打开光标 */  
		OPEN _Cur; 
		REPEAT  
				FETCH _Cur INTO domain_id;
				SET log_info=CONCAT(domain_id,",",log_info);
				IF NOT _done THEN 
					#最快
					SELECT r.total_time,r.ipaddr_id,r.size_download,r.speed_download,r.redirect_count INTO fastest_time,fastest_ip_id,fastest_size,fastest_speed,fastest_redirect FROM domain_result r,domain_domain d where r.domain_id=d.id and r.create_time>now()- INTERVAL interval_time MINUTE and d.id=domain_id and r.total_time>0 order by r.total_time LIMIT 1;														
					#最慢
					SELECT r.total_time,r.ipaddr_id,r.create_time,r.size_download,r.speed_download,r.redirect_count INTO slowest_time,slowest_ip_id,create_time,slowest_size,slowest_speed,slowest_redirect FROM domain_result r,domain_domain d where r.domain_id=d.id and r.create_time>now()- INTERVAL interval_time MINUTE and d.id=domain_id order by r.total_time DESC LIMIT 1;					
					IF NOT slowest_time IS NULL and NOT fastest_time IS NULL THEN
							#插入状态表
							INSERT INTO domain_responsestatus (ipaddr_id,proxy_id,domain_id,http_code,total_time,create_time,status) SELECT a.ipaddr_id,a.proxy_id,a.domain_id,a.http_code,a.total_time,a.create_time,a.status FROM domain_result as a where a.domain_id=domain_id and a.create_time>now()- INTERVAL interval_time MINUTE;							
							#插入最快最慢表
							INSERT INTO domain_responsetime (slowest_ip_id,fastest_ip_id,slowest_time,fastest_time,domain_id,create_time,status,fastest_size,fastest_speed,fastest_redirect,slowest_size,slowest_speed,slowest_redirect) VALUES (slowest_ip_id,fastest_ip_id,slowest_time,fastest_time,domain_id,create_time,1,fastest_size,fastest_speed,fastest_redirect,slowest_size,slowest_speed,slowest_redirect);													
					END IF;								
					SET _done = 0;
				END IF;  
		UNTIL _done END REPEAT; #当_done=1时退出被循 
		insert into domain_log (log) SELECT log_info;
		insert into domain_log (log) SELECT concat('end time:',now());
		/*关闭光标*/  
		CLOSE _Cur; 
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-03-18 15:45:02
