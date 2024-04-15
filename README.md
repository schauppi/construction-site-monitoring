# construction-site-monitoring

source construction_site_monitoring/bin/activate

https://wiki.seeedstudio.com/YOLOv8-DeepStream-TRT-Jetson/

no - ip: 

sudo systemctl status dnsmasq

cat /var/lib/misc/dnsmasq.leases

NTP Server:
curl -X POST -i 'http://192.168.2.113/cgi-bin/api.cgi?cmd=SetNtp&user=cam2&password=XXX' --data '[
{
"cmd":"SetNtp",
"param":{
"Ntp":{
"enable":1,
"server":"192.168.50.137",
"port":123,
"interval":1440
}
}
}
]'
