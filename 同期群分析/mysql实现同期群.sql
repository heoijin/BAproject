-- 步骤一：筛选订单状态为”交易成功“的行，并输出表sheet2：用户昵称【c_id】、付款时间【paytime】
CREATE table sheet2 as
SELECT c_id,paytime
FROM sheet1
WHERE `status`='交易成功';


-- 步骤二：找出每个用户的首单时间
SELECT c_id,min(paytime) f_time
FROM sheet2
GROUP BY c_id;


-- 步骤三：求出月份差，对首付时间进行重采样
SELECT 
	a.c_id,
	b.f_time,
	TIMESTAMPDIFF(MONTH,b.f_time,a.paytime) m_diff,
	CONCAT(YEAR(b.f_time),"年",MONTH(b.f_time),"月") y_m
from sheet2 a
LEFT JOIN (
	SELECT c_id,min(paytime) f_time
	FROM sheet2
	GROUP BY c_id
-- 	LIMIT测试时用，为了提升效率
	LIMIT 0,7000
) b on a.c_id=b.c_id
-- 同样是为了提升效率而使用
WHERE b.f_time is NOT NULL;


-- 步骤四：通过首付时间和月份差进行分组，求出唯一的用户id数,并输出为表[cohort]
CREATE table cohort as
SELECT c.y_m "首付月份",c.m_diff"月份差",COUNT(DISTINCT c.c_id) "留存量"
FROM (
SELECT 
	a.c_id,
	b.f_time,
	TIMESTAMPDIFF(MONTH,b.f_time,a.paytime) m_diff,
	CONCAT(YEAR(b.f_time),"年",MONTH(b.f_time),"月") y_m
from sheet2 a
LEFT JOIN (
	SELECT c_id,min(paytime) f_time
	FROM sheet2
	GROUP BY c_id
) b on a.c_id=b.c_id
-- 为了提升效率而使用
WHERE b.f_time is NOT NULL
) c
GROUP BY c.y_m,c.m_diff;

-- 步骤五：计算留存率
SELECT c.`首付月份`,CONCAT(ROUND((c.`留存量`/m.`留存量`)*100,2),"%") 留存率
FROM cohort c
LEFT JOIN (
SELECT 首付月份,留存量
FROM cohort
where `月份差`=0
) m 
on c.`首付月份`=m.`首付月份`;