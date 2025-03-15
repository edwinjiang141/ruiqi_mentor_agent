# HBA Card 或 HBA Controller 性能故障

## 流程步骤
1. **ASR 警告**：系统检测到 ASR 警告。
2. **判断条件**：符合判断条件采取应急措施。
3. **更换硬件**：如果需要，进行硬件更换。

## 故障节点

- **Offline Cell 故障节点**：检查是否存在 Offline Cell 故障。参考如下步骤
Steps to shut down or reboot an Exadata storage cell without affecting ASM (Doc ID 1188080.1)
1.	检查和调大每个Diskgroup 的disk_repair_time 设置，默认值是3.6小时，如果cell node offline 超过这个值，该cell上所有ASM disk会被强制删除。
SQL> select dg.name,a.value from v$asm_diskgroup dg, v$asm_attribute a where dg.group_number=a.group_number and a.name='disk_repair_time';
SQL> ALTER DISKGROUP DATA SET ATTRIBUTE 'DISK_REPAIR_TIME'='8.5H';<<-------根据需要调大disk_repair_time 的设置。
2.	12c 之后的高版本，ASM DG 引入一个新属性 failgroup_repair_time，默认值是24H，该参数控制Diskgroup 的failure group 维护时间，如果DG 中的failgroup Offline 超过了该值，将被强制drop。
SQL> select dg.name,a.value from v$asm_diskgroup dg, v$asm_attribute a where dg.group_number=a.group_number and a.name=' failgroup_repair_time ';
SQL> alter diskgroup <failure_group> set attribute 'failgroup_repair_time'='30H'; <<-------根据需要调大failgroup_repair_time 的设置。

3.	如果grid disk offline 后，grid disk输出应该是asmdeactivationoutcome=’YES’ 否则是NO, asmmodestatus 应该是 ONLINE
# cellcli    <<<<<<<< cell 节点执行cellcli 进入到 CeLLCLI> 命令行
CellCLI> list griddisk attributes name,asmmodestatus,asmdeactivationoutcome

4.	Cell node poweroff 前，需要把grid disk offline，下面是offline grid disk 命令：
CellCLI> CellCLI -e alter griddisk all inactive
5.	检查grid disk 状态是offline, asmmodestatus 应该是 UNUSED or OFFLINE ，asmdeactivationoutcome 应该是YES，如果不是Yes，等待和重复检查，直到asmdeactivationoutcome=’YES’ ，并且用 list griddisk 确保状态都是inactive
CellCLI> list griddisk attributes name,asmmodestatus,asmdeactivationoutcome
CellCLI> list griddisk

6.	关闭 cell node OS
# shutdown -h now
7.	重启 cell node,一旦操作系统完成启动后，手工拉起grid disks，并所有grid disk 状态是 active 
CellCLI> alter griddisk all active
CellCLI> list griddisk

8.	检查所有grid disk的状态是ONLINE
CellCLI> list griddisk attributes name, asmmodestatus

- **故障信息收集**：
收集 Sundiag output。
登陆到目标 cell节点
# /opt/oracle.SupportTools/sundiag.sh   <<<<<< 单服务器收集命令
# dcli -g all_group -l root /opt/oracle.SupportTools/sundiag.sh 2>&1 (备注：dcli 命令实现单次完成所有节点的sundiag 日志收集，需要配置节点间root 信任关系，如果不允许配置节点间的信任关系，利用上面的命令逐台机器收集。另外，这种方式仅是集中采集,生成的sundiag output 存放在各自服务器上。)


## HBSC 一体机故障应急预案
- 如果存在 Offline Cell 故障，则进行 HangDown 判断。

## HangDown 处理流程
1. **容灾切换 Switchover**：尝试进行容灾切换。
2. **Switchover 失败**：如果切换失败，进入下一步。
3. **容灾切换 Failover**：进行容灾切换。
4. **结束**：完成处理流程。