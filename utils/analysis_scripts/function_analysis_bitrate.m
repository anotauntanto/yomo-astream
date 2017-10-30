
function function_analysis_bitrate(filename)

%% Configuration

%filename = 'test.json';
font_size = 14;

ax1_position = [0 0 1 1];
ax2_position = [.45 .1 .5 .8];

textbox_x1 = .025;
textbox_y1 = 0.7;
textbox_x2 = .025;
textbox_y2 = 0.35;

bitrates_delimiter = ';';

%% Reading Input

filetext = fileread(filename);
jsonvalue = jsondecode(filetext);

cnf_tag = get_field_str(jsonvalue,'cnf_tag');
container_version = get_field_str(jsonvalue,'ContainerVersion');
data_id = get_field_str(jsonvalue,'DataId');
node_id = get_field_str(jsonvalue,'NodeId');
timestamp = get_field_str(jsonvalue,'Time');

mcc_mnc_nw = get_field_num(jsonvalue,'NWMCCMNC');
mcc_mnc_sim = get_field_num(jsonvalue,'IMSIMCCMNC');
cnf_astream_segment_limit = get_field_num(jsonvalue,'cnf_astream_segment_limit');
cnf_yomo_playback_duration_s = get_field_num(jsonvalue,'cnf_yomo_playback_duration_s');

cnf_q1 = get_field_num(jsonvalue,'cnf_q1');
cnf_q2 = get_field_num(jsonvalue,'cnf_q2');
cnf_q3 = get_field_num(jsonvalue,'cnf_q3');
cnf_q4 = get_field_num(jsonvalue,'cnf_q4');

res_astream_available_bitrates = get_field_str(jsonvalue,'res_astream_available_bitrates');

res_yomo_bitrate_mean = get_field_num(jsonvalue,'res_yomo_bitrate_mean');
res_yomo_bitrate_max = get_field_num(jsonvalue,'res_yomo_bitrate_max');
res_yomo_bitrate_min = get_field_num(jsonvalue,'res_yomo_bitrate_min');
res_yomo_bitrate_q1 = get_field_num(jsonvalue,'res_yomo_bitrate_q1');
res_yomo_bitrate_q2 = get_field_num(jsonvalue,'res_yomo_bitrate_q2');
res_yomo_bitrate_q3 = get_field_num(jsonvalue,'res_yomo_bitrate_q3');
res_yomo_bitrate_q4 = get_field_num(jsonvalue,'res_yomo_bitrate_q4');

res_astream_bitrate_mean = get_field_num(jsonvalue,'res_astream_bitrate_mean');
res_astream_bitrate_max = get_field_num(jsonvalue,'res_astream_bitrate_max');
res_astream_bitrate_min = get_field_num(jsonvalue,'res_astream_bitrate_min');
res_astream_bitrate_q1 = get_field_num(jsonvalue,'res_astream_bitrate_q1');
res_astream_bitrate_q2 = get_field_num(jsonvalue,'res_astream_bitrate_q2');
res_astream_bitrate_q3 = get_field_num(jsonvalue,'res_astream_bitrate_q3');
res_astream_bitrate_q4 = get_field_num(jsonvalue,'res_astream_bitrate_q4');

%% Plots

%close all
figure;

if isnan(cnf_q1) || isnan(cnf_q2) || isnan(cnf_q3) || isnan(cnf_q4)
    str_q1 = 'Q1';
    str_q2 = 'Q2';
    str_q3 = 'Q3';
    str_q4 = 'Q4';
else
    str_q1 = ['Q1: ',num2str(cnf_q1)];
    str_q2 = ['Q2: ',num2str(cnf_q2)];
    str_q3 = ['Q3: ',num2str(cnf_q3)];
    str_q4 = ['Q4: ',num2str(cnf_q4)];
end

descr_bitrates = strsplit(res_astream_available_bitrates,bitrates_delimiter);

descr = {['Time: ',timestamp],...%strcat('Time: ',timestamp);
    ['Container Version: ',container_version],...
    ['Node ID: ',node_id],...
    ['MCCMNC (SIM): ',mcc_mnc_sim],...
    ['MCCMNC (NW): ',mcc_mnc_nw],...
    ['AStream Segment Limit: ',cnf_astream_segment_limit],...
    ['YoMo Playback Duration: ',cnf_yomo_playback_duration_s],...
    '',...
    'Available Bitrates: '};

yomo_stacked = [res_yomo_bitrate_mean;
    res_yomo_bitrate_max;
    res_yomo_bitrate_min;
    res_yomo_bitrate_q1;
    res_yomo_bitrate_q2;
    res_yomo_bitrate_q3;
    res_yomo_bitrate_q4];

astream_stacked = [res_astream_bitrate_mean;
    res_astream_bitrate_max;
    res_astream_bitrate_min;
    res_astream_bitrate_q1;
    res_astream_bitrate_q2;
    res_astream_bitrate_q3;
    res_astream_bitrate_q4];

%fig = figure;
ax1 = axes('Position',ax1_position,'Visible','off');
ax2 = axes('Position',ax2_position);

bar(ax2,[yomo_stacked,astream_stacked])
xticklabels({'mean','max','min',str_q1,str_q2,str_q3,str_q4});
h = legend('YoMo','AStream');
legend('show')
set(gca,'FontSize',font_size)
set(h,'FontSize',font_size)

title_str = 'Bitrate (Kbit/s)';
title(title_str);

axes(ax1)
t1 = text(textbox_x1,textbox_y1,descr);
t1.FontSize = font_size;

axes(ax1)
t2 = text(textbox_x2,textbox_y2,descr_bitrates);
t2.FontSize = font_size;

end

%% Helper Functions

function str_out = get_field_str(json_in,str_in)
try
    value_str = getfield(json_in,str_in);
    if strcmp(value_str,'NA') || strcmp(value_str,'None') || isempty(value_str)
        str_out='NA';
    else
        str_out = value_str;
    end
catch ME
    str_out = 'NA';
end
end

function num_out = get_field_num(json_in,str_in)
try
    value_str = getfield(json_in,str_in);
    if strcmp(value_str,'NA') || strcmp(value_str,'None') || isempty(value_str)
        num_out=NaN;
    else
        num_out=str2num(value_str);
    end
catch ME
    num_out = NaN;
end
end