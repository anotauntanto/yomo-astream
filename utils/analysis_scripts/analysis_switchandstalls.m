
filename='DASH_BUFFER_LOG_2017-08-07.00_15_24.csv';
data = read_mixed_csv(filename,',');

segment_duration=5;

data_filtered=data(2:end,:);
epoch_time=cell2mat(cellfun(@str2num,data_filtered(:,1),'un',0));
playback_time=cell2mat(cellfun(@str2num,data_filtered(:,2),'un',0));
playback_state=data_filtered(:,4);
action=data_filtered(:,5);
bitrate=cell2mat(cellfun(@str2num,data_filtered(:,6),'un',0));

indices_buffering=cellfun(@(x)~isempty(strfind(x,'BUFFERING')), playback_state);
indices_playing=cellfun(@(x)~isempty(strfind(x,'PLAY')), playback_state);
indices_stopping=cellfun(@(x)~isempty(strfind(x,'STOP')), playback_state);
indices_writing=cellfun(@(x)~isempty(strfind(x,'Writing')), action);
indices_transition=cellfun(@(x)~isempty(strfind(x,'-')), action);

% isnotbuffering=~(indices_buffering & ~indices_transition);
% iswriting=indices_writing;
% isplaying=((indices_playing | indices_stopping | indices_play_buffering) & ~indices_transition);

buffer=[str2num(data_filtered{1,3})];

for i=2:size(data_filtered,1)
    isnotbuffering=~(indices_buffering(i)==1 & indices_transition(i)~=1);
    iswriting=(indices_writing(i)==1);
    isplaying=(((indices_playing(i)==1 | indices_stopping(i)==1) & indices_transition(i)~=1)) | (indices_buffering(i)==1 | indices_transition(i)==1 ) ;
    current_buffer=isnotbuffering*buffer(i-1)+iswriting*segment_duration-isplaying*(epoch_time(i)-epoch_time(i-1));
    buffer=[buffer;current_buffer];
end