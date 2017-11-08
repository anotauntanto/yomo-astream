function bandwidth = getBandwidth( path )
%     disp(path);
    data = loadTsharkLogFile( path );
    throughput = 0;
    throughputList = [];
    timestamps = [];
    
    if isempty(data)
        bandwidth = [];
        return;
    end
    
    lastTimestamp = str2double(data{1,1});
    
    for i=1:length(data)

       timestamp = str2double(data{i,1});
       currThroughput = str2double(data{i,3});
       if isnan(currThroughput) && i ~= length(data)
           continue;
       end       

       if timestamp == lastTimestamp
               throughput = throughput + currThroughput;
       else 
           diff = timestamp - lastTimestamp;
           for j=1:diff-1
               throughputList = [throughputList, 0];
               timestamps = [timestamps, timestamp];
           end
           throughputList = [throughputList, throughput];
           timestamps = [timestamps, timestamp];
           throughput = currThroughput;
           lastTimestamp = timestamp; 
       end
    end  
        
    bandwidth = [throughputList; timestamps];
    
end