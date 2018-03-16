SELECT `imsimccmnc`,`nwmccmnc`, 
year(FROM_UNIXTIME(`timestamp`))as `year`,
month(FROM_UNIXTIME(`timestamp`))as `month`,
count(*) as `num_samples`,
max(`res_dl_throughput_kbps`)/1000 as `max_dl_mbps`,
min(`res_dl_throughput_kbps`)/1000 as `min_dl_mbps`,
avg(`res_dl_throughput_kbps`)/1000 as `mean_dl_mbps`,
max(`res_ul_throughput_kbps`)/1000 as `max_ul_mbps`,
min(`res_ul_throughput_kbps`)/1000 as `min_ul_mbps`,
avg(`res_ul_throughput_kbps`)/1000 as `mean_ul_mbps`,
max(`res_rtt_tcp_payload_client_ns`)/1000000 as `max_rtt_ms`,
min(`res_rtt_tcp_payload_client_ns`)/1000000 as `min_rtt_ms`,
avg(`res_rtt_tcp_payload_client_ns`)/1000000 as `mean_rtt_ms`
FROM monroe.monroe_exp_nettest
WHERE (`timestamp` BETWEEN 1504224001 AND 1519862401) #01.09.2017-01.03.2018
AND (`res_status`="success")
GROUP BY `imsimccmnc`,`nwmccmnc`,`year`, `month`
ORDER BY `year`,`month`, count(*) DESC;