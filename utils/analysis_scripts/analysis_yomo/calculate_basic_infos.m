% Calculate basic evaluations per ZTId

%% get files MONROE

clear all;

ytIds = {'D8YQn7o_AyA','6v2L2UGZJAM','Y-rmzh0PI3c','N2sCbtodGMI'};

dataLogsPathsAll = rdir('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/*yomo_buffer.txt');
eventLogsPathsAll = rdir('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/*yomo_events.txt');
tsharkLogsPathsAll = rdir('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/*yomo_tshark_.txt');

% dataLogsPathsID1 = rdir(strcat('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/YT_', ytIds{1} ,'_*buffer.txt'));
% eventLogsPathsID1 = rdir(strcat('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/YT_', ytIds{1} ,'_*events.txt'));
% dataLogsPathsID2 = rdir(strcat('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/YT_', ytIds{2} ,'_*buffer.txt'));
% eventLogsPathsID2 = rdir(strcat('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/YT_', ytIds{2} ,'_*events.txt'));
% dataLogsPathsID3 = rdir(strcat('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/YT_', ytIds{3} ,'_*buffer.txt'));
% eventLogsPathsID3 = rdir(strcat('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/YT_', ytIds{3} ,'_*events.txt'));
% dataLogsPathsID4 = rdir(strcat('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/YT_', ytIds{4} ,'_*buffer.txt'));
% eventLogsPathsID4 = rdir(strcat('/home/anika/Dokumente/Projekte/yomo/yomo-astream/data/YT_', ytIds{4} ,'_*events.txt'));

subindex = @(A,r,c) A(r,c);      %# An anonymous function to index a matrix



%% get files local
% 
% clear all;
% 
% ytIds = {'D8YQn7o_AyA','6v2L2UGZJAM','Y-rmzh0PI3c','N2sCbtodGMI'};
% 
% dataLogsPathsAll = rdir('./**/2017-10_local_runs/**/YT_*buffer.txt');
% eventLogsPathsAll = rdir('./**/2017-10_local_runs/**/YT_*events.txt');
% tsharkLogsPathsAll = rdir('./**/2017-10_local_runs/**/YT_tshark__*.txt');
% 
% dataLogsPathsID1 = rdir(strcat('./**/2017-10_local_runs/**/YT_', ytIds{1} ,'_*buffer.txt'));
% eventLogsPathsID1 = rdir(strcat('./**/2017-10_local_runs/**/YT_', ytIds{1} ,'_*events.txt'));
% dataLogsPathsID2 = rdir(strcat('./**/2017-10_local_runs/**/YT_', ytIds{2} ,'_*buffer.txt'));
% eventLogsPathsID2 = rdir(strcat('./**/2017-10_local_runs/**/YT_', ytIds{2} ,'_*events.txt'));
% dataLogsPathsID3 = rdir(strcat('./**/2017-10_local_runs/**/YT_', ytIds{3} ,'_*buffer.txt'));
% eventLogsPathsID3 = rdir(strcat('./**/2017-10_local_runs/**/YT_', ytIds{3} ,'_*events.txt'));
% dataLogsPathsID4 = rdir(strcat('./**/2017-10_local_runs/**/YT_', ytIds{4} ,'_*buffer.txt'));
% eventLogsPathsID4 = rdir(strcat('./**/2017-10_local_runs/**/YT_', ytIds{4} ,'_*events.txt'));
% 
% subindex = @(A,r,c) A(r,c);      %# An anonymous function to index a matrix

%% logging start delay
startDelays = arrayfun(@(x) getLoggingStartDelay(x.name), dataLogsPathsAll);
meanStartDely = mean(startDelays);

% startDelaysID1 = arrayfun(@(x) getLoggingStartDelay(x.name), dataLogsPathsID1);
% startDelaysID2 = arrayfun(@(x) getLoggingStartDelay(x.name), dataLogsPathsID2);
% startDelaysID3 = arrayfun(@(x) getLoggingStartDelay(x.name), dataLogsPathsID3);
% startDelaysID4 = arrayfun(@(x) getLoggingStartDelay(x.name), dataLogsPathsID4);

%% stalling

stallingLength = arrayfun(@(x) sum(getStallingDurations(x.name)), dataLogsPathsAll);
stallingCount = arrayfun(@(x) length(getStallingDurations(x.name)), dataLogsPathsAll);


% stallingLengthID1 = arrayfun(@(x) sum(getStallingDurations(x.name)), dataLogsPathsID1);
% stallingCountID1 = arrayfun(@(x) length(getStallingDurations(x.name)), dataLogsPathsID1);
% stallingLengthID2 = arrayfun(@(x) sum(getStallingDurations(x.name)), dataLogsPathsID2);
% stallingCountID2 = arrayfun(@(x) length(getStallingDurations(x.name)), dataLogsPathsID2);
% stallingLengthID3 = arrayfun(@(x) sum(getStallingDurations(x.name)), dataLogsPathsID3);
% stallingCountID3 = arrayfun(@(x) length(getStallingDurations(x.name)), dataLogsPathsID3);
% stallingLengthID4 = arrayfun(@(x) sum(getStallingDurations(x.name)), dataLogsPathsID4);
% stallingCountID4 = arrayfun(@(x) length(getStallingDurations(x.name)), dataLogsPathsID4);

%% qualities and quality switches

[upSwitches, downSwitches, qualities] = arrayfun(@(x) getQualitySwitches(x.name), eventLogsPathsAll,'un',0);

qualSwitchesMeanAll = arrayfun(@length, qualities);


%% bandwidth

bandwidth = arrayfun(@(x) getBandwidth(x.name), tsharkLogsPathsAll,'un',0);

%% plot bandwidth

figure(5);
hold all;
plot(bandwidth{1,1}(1,:)*8/1000/1000);
ylabel('tcp length [Mbps]');
xlabel('time since start of tshark [s]');


%% buffer

[bufferAll] = arrayfun(@(x) getBuffer(x.name), dataLogsPathsAll,'un',0);
% [bufferID1] = arrayfun(@(x) getBuffer(x.name), dataLogsPathsID1,'un',0);
% [bufferID2] = arrayfun(@(x) getBuffer(x.name), dataLogsPathsID2,'un',0);
% [bufferID3] = arrayfun(@(x) getBuffer(x.name), dataLogsPathsID3,'un',0);
% [bufferID4] = arrayfun(@(x) getBuffer(x.name), dataLogsPathsID4,'un',0);

%% mean,max buffer

subindex = @(A,r,c) A(r,c);      %# An anonymous function to index a matrix

bufferMeanAll = cell2mat(arrayfun(@(x) subindex(mean(getBuffer(x.name)),1,3), dataLogsPathsAll,'un',0));
% [bufferMeanID1] = cell2mat(arrayfun(@(x) subindex(mean(getBuffer(x.name)),1,3), dataLogsPathsID1,'un',0));
% [bufferMeanID2] = cell2mat(arrayfun(@(x) subindex(mean(getBuffer(x.name)),1,3), dataLogsPathsID2,'un',0));
% [bufferMeanID3] = cell2mat(arrayfun(@(x) subindex(mean(getBuffer(x.name)),1,3), dataLogsPathsID3,'un',0));
% [bufferMeanID4] = cell2mat(arrayfun(@(x) subindex(mean(getBuffer(x.name)),1,3), dataLogsPathsID4,'un',0));

bufferMaxAll = cell2mat(arrayfun(@(x) subindex(max(getBuffer(x.name)),1,3), dataLogsPathsAll,'un',0));
% [bufferMaxID1] = cell2mat(arrayfun(@(x) subindex(max(getBuffer(x.name)),1,3), dataLogsPathsID1,'un',0));
% [bufferMaxID2] = cell2mat(arrayfun(@(x) subindex(max(getBuffer(x.name)),1,3), dataLogsPathsID2,'un',0));
% [bufferMaxID3] = cell2mat(arrayfun(@(x) subindex(max(getBuffer(x.name)),1,3), dataLogsPathsID3,'un',0));
% [bufferMaxID4] = cell2mat(arrayfun(@(x) subindex(max(getBuffer(x.name)),1,3), dataLogsPathsID4,'un',0));

%% plot buffer

figure(1);
hold all;
arrayfun(@(x) plot(x{1}(:,1)-x{1}(1,1)+x{1}(1,2),x{1}(:,3)), bufferAll,'un',0);
ylabel('buffered playback time [s]');
xlabel('time since start of the video [s]');


% figure(1);
% hold all;
% arrayfun(@(x) plot(x{1}(:,1)-x{1}(1,1)+x{1}(1,2),x{1}(:,3)), bufferID1,'un',0);
% ylabel('buffered playback time [s]');
% xlabel('time since start of the video [s]');
% 
% figure(2);
% hold all;
% arrayfun(@(x) plot(x{1}(:,1)-x{1}(1,1)+x{1}(1,2),x{1}(:,3)), bufferID2,'un',0);
% ylabel('buffered playback time [s]');
% xlabel('time since start of the video [s]');
% 
% figure(3);
% hold all;
% arrayfun(@(x) plot(x{1}(:,1)-x{1}(1,1)+x{1}(1,2),x{1}(:,3)), bufferID3,'un',0);
% ylabel('buffered playback time [s]');
% xlabel('time since start of the video [s]');
% 
% figure(4);
% hold all;
% arrayfun(@(x) plot(x{1}(:,1)-x{1}(1,1)+x{1}(1,2),x{1}(:,3)), bufferID4,'un',0);
% ylabel('buffered playback time [s]');
% xlabel('time since start of the video [s]');






