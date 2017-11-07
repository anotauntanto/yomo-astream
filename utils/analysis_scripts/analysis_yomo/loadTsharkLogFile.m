function tSharkData = loadTsharkLogFile( path )
    
    r=1;
    fid = fopen(path);
    tline = fgetl(fid);
    tSharkData = {};
    while ischar(tline)
        data = regexp(tline,',','split');
        tf = cellfun('isempty',data);
        data(tf) = {'0'};
        if (length(data) < 5)
            break;
        end
%         timestampSplit = data{1};
%         timestamp = str2double(strcat(timestampSplit(1:10),timestampSplit(12:14)));
%         if timestamp < video.StartTimeRequ
%             tline = fgetl(fid);
%             continue;
%         elseif timestamp > video.EndTime
%             break;
%         end
        
        tSharkData(r,2) = data(2);
        tSharkData(r,3) = data(3);
        tSharkData(r,1) = extractBefore(data(1),".");
        tSharkData(r,4) = data(4);
        tSharkData(r,5) = data(5);

        tline = fgetl(fid); 
        r = r+1; 
    end
    fclose(fid);
    
end