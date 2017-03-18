CREATE DEFINER = `root`@`localhost` PROCEDURE `record_backup`()
BEGIN
		/*
			表domain_result数据每2分钟拷贝至表domain_responsestatus,表domain_responsetime
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

		DECLARE CONTINUE HANDLER FOR SQLSTATE '02501' SET _done = 1;#错误定义，标记循环结束 
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
				END IF;  
    UNTIL _done END REPEAT; #当_done=1时退出被循 
		/*关闭光标*/  
    CLOSE _Cur;  
END;

