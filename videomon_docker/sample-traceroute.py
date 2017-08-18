#sample traceroute function
#can be used within run_yomo and run_astream

def traceroute(target, interface):
    cmd = ['traceroute', '-A']
    if (interface):
        cmd.extend(['-i', interface])
    cmd.append(target)
    print("doing traceroute...")
    time_start = time.time()
    p = Popen(cmd, stdout=PIPE)
    data = p.communicate()[0]
    time_end = time.time()
    print("traceroute finished.")
    #print("traceroute: {}".format(data))
    try:
        traceroute = parse_traceroute(data)
    except Exception as e:
        traceroute = {'error': 'could not parse traceroute'}
    if not traceroute:
        traceroute = {'error': 'no traceroute output'}
    traceroute['time_start'] = time_start
    traceroute['time_end'] = time_end
    traceroute['raw'] = data.decode('ascii', 'replace')
    with NamedTemporaryFile(mode='w+', prefix='tmptraceroute', suffix='.json', delete=False) as f:
        f.write(json.dumps(traceroute))
        return f.name
