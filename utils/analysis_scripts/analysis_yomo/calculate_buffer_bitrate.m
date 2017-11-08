%%
clear all; 
experimentId = 414124;

dataLogPath = rdir(strcat('./**/2017-10-05_base_eval/**/', num2str(experimentId) ,'/*buffer.txt'));
eventLogPath = rdir(strcat('./**/2017-10-05_base_eval/**/', num2str(experimentId) ,'/*events.txt'));
tsharkLogPath = rdir(strcat('./**/2017-10-05_base_eval/**/', num2str(experimentId) ,'/YT_tshark__*.txt'));

buffer = getBuffer(dataLogPath.name);
bandwidth = getBandwidth(tsharkLogPath.name);

videoStartTime = buffer(1,1)/1000-buffer(1,2);
videoEndTime = buffer(end,1)/1000;

%%

% plot bandwidth
figure(1);
hold all;
yyaxis left
plot(bandwidth(2,:)-videoStartTime, bandwidth(1,:)*0.008);
ylabel('bandwidth [kbps]');
xlabel('time since start of tshark [s]');

% plot buffer
yyaxis right
plot(buffer(:,1)/1000-videoStartTime,buffer(:,3));
ylabel('buffered playback time [s]');

xlim([-50,videoEndTime-videoStartTime])