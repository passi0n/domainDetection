# domainDetection 域名探测系统
#作用： 该系统主要用于对网页访问业务的域名解析和互通进行探测和监控。

#原理：该系统基于python3.0+django 1.8+highcharts,可分为三个部分，第一个部分为探针脚本，第二个部分为后台管理部分，第三个部分为前台展示部分。

#探针部分： 对配置的域名进行dig命令探测出目标ip，然后采用pycurl模块对域名的不同目标ip出口进行互通探测，将采集的目标ip，http状态码，访问时长，下载大小，下载速度，跳转次数，ip归属地进行入库操作。

#后台管理部分：采用django+mysql,django主要进行域名配置，数据库设计部分采用分层设计即基础数据层和业务层。探针脚本将基础数据采集到数据表，存储过程定时对基础数据表中数据进行过滤录入到业务表。业务表为http状态表和响应时间表。

#前台部分：采用highcharts 图表进行展示，首页分页展示每个域名单次响应时长，1h平均响应时长，1h异常数，1h超时数，以及1d统计项（与1h相关项一致）。域名详细页：展示每个域名2天时间的域名响应状态图表和响应时间图表
