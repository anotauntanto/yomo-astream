function stallingDurations = getStallingDurations( path )

    data = loadDataLogFile( path );
    diffTimestamps = diff(data(:,1))/1000;
    diffPlaytimes = diff(data(:,2));
    endIndex = find(diffPlaytimes <= 0);
    if (isempty(endIndex))
       endIndex = length(diffTimestamps);
    end
    diffTimePlay = diffTimestamps(1:endIndex-1)-diffPlaytimes(1:endIndex-1);

    stallingIndices = find(diffTimePlay > 0.5);
    stallingDurations = arrayfun(@(x) diffTimePlay(x), stallingIndices);

end

