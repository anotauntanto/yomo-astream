
%% Configuration

filename = 'test.json';
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

res_yomo_numswitches_up = get_field_num(jsonvalue,'res_yomo_numswitches_up');
res_yomo_numswitches_down = get_field_num(jsonvalue,'res_yomo_numswitches_down');
res_astream_numswitches_up = get_field_num(jsonvalue,'res_astream_numswitches_up');
res_astream_numswitches_down = get_field_num(jsonvalue,'res_astream_numswitches_down');

%% Plots

close all

descr_bitrates = strsplit(res_astream_available_bitrates,bitrates_delimiter);

descr = {['Time: ',timestamp],...%strcat('Time: ',timestamp);
    ['Container Version: ',container_version],...
    ['Node ID: ',node_id],...
    ['MCCMNC (SIM): ',num2str(mcc_mnc_sim)],...
    ['MCCMNC (NW): ',num2str(mcc_mnc_nw)],...
    ['AStream Segment Limit: ',num2str(cnf_astream_segment_limit)],...
    ['YoMo Playback Duration: ',num2str(cnf_yomo_playback_duration_s)],...
    '',...
    'Available Bitrates: '};

yomo_stacked = [res_yomo_numswitches_up;
    res_yomo_numswitches_down];

astream_stacked = [res_astream_numswitches_up;
    res_astream_numswitches_down];

fig = figure;
ax1 = axes('Position',ax1_position,'Visible','off');
ax2 = axes('Position',ax2_position);

bar(ax2,[yomo_stacked,astream_stacked])
xticklabels({'up','down'});
h = legend('YoMo','AStream');
legend('show')
set(gca,'FontSize',font_size)
set(h,'FontSize',font_size)

title_str = 'Number of Switches';
title(title_str);

axes(ax1)
t1 = text(textbox_x1,textbox_y1,descr);
t1.FontSize = font_size;

axes(ax1)
t2 = text(textbox_x2,textbox_y2,descr_bitrates);
t2.FontSize = font_size;

%% Functions

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
    if ischar(value_str)
        if strcmp(value_str,'NaN') || strcmp(value_str,'None') || isempty(value_str)
            num_out = NaN;
        else
            num_out = str2num(value_str);
        end
        
    elseif isnumeric(value_str)
            num_out = value_str;
    end
catch ME
    %disp(ME)
    num_out = NaN;
end
end