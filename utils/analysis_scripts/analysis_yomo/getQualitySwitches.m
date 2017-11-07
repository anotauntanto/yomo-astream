function [upSwitches, downSwitches, qualities] = getQualitySwitches( path )

    data = loadEventLogFile( path );
    endIndex = min(find(strcmp(data{1,2},'ended')>0),length(data{1,2}));
    events = data{1,2}(1:endIndex);
    qualitySwitchesIndices = find(contains(events,'quality')>0);
    qualities = arrayfun(@(x) extractBetween(events(x),"quality:","p "), qualitySwitchesIndices);
    
    up = 0;
    down = 0;
    i = [2:length(qualities)];
    if (length(qualities)>1)
        up = arrayfun(@(x) str2num(qualities{x})>str2num(qualities{x-1}), i);
        down = arrayfun(@(x) str2num(qualities{x})<str2num(qualities{x-1}), i);
    end
    
    upSwitches = sum(up>0);
    downSwitches = sum(down>0);
    
    end