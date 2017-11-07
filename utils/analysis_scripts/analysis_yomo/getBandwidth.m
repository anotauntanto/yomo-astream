function throughputList = getBandwidth( path )
%     disp(path);
    data = loadTsharkLogFile( path );
    throughput = 0;
    throughputList = [];
    
    if isempty(data)
        throughputList = [];
        return;
    end
    
    lastTimestamp = str2double(data{1,1});
    
    for i=1:length(data)

       timestamp = str2double(data{i,1});
       currThroughput = str2double(data{i,2});
       if isnan(currThroughput) && i ~= length(data)
           continue;
       end       

       if timestamp == lastTimestamp
               throughput = throughput + currThroughput;
       else 
           diff = timestamp - lastTimestamp;
           for j=1:diff-1
               throughputList = [throughputList, 0];
           end
           throughputList = [throughputList, throughput];
           throughput = currThroughput;
           lastTimestamp = timestamp; 
       end
    end  
        
end