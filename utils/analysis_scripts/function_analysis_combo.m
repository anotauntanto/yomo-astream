function function_analysis_combo(indir,outdir,campaign_tag)

% outdir = '/Users/cmidoglu/Downloads/videomon_MATLAB_results_campaign4';
% campaign_tag = 'campaign1';

files = dir(indir);
directoryNames = {files([files.isdir]).name};
directoryNames = directoryNames(~ismember(directoryNames,{'.','..'}));

for i = 1:length(directoryNames)
    folder = directoryNames{i};
    folderpath = strcat(indir,'/',folder);
    files = dir(folderpath);
    fileNames = {files.name};
    for j=1:length(fileNames)
        file=fileNames{j};
        if strfind(file, '_summary.json')
            filepath = strcat(folderpath,'/',file)
            function_analysis_combo_helper(folder,filepath,outdir,campaign_tag);
        end
        
    end
    
end

end
%outfile=strcat(campaign,time,bitrate/buffer/durstalls)

%% Helper Functions

function function_analysis_combo_helper(foldername,filename,outdir,campaign_tag)
%% Configuration

%filename = 'test.json';
%filename = 'test2.json';
%outdir = '/Users/cmidoglu/Downloads/videomon_MATLAB_test';
%campaign_tag = 'campaign1';

font_size = 14;
bitrates_delimiter = ';';

pos_bitrate = [0.3 0.6 0.3 0.3];
pos_buffer = [0.3 0.1 0.3 0.3];
pos_durstalls = [0.65 0.1 0.3 0.3];
pos_numswitches = [0.65 0.6 0.3 0.3];
pos_description = [0.05 0.1 0.1 0.8];

textbox_x = 0;
textbox_y = .5;

%% Reading Input

filetext = fileread(filename);
jsonvalue = jsondecode(filetext);

%cnf_tag = get_field_str(jsonvalue,'cnf_tag');
timestamp = get_field_str(jsonvalue,'Time');
container_version = get_field_str(jsonvalue,'ContainerVersion');
%data_id = get_field_str(jsonvalue,'DataId');

node_id = get_field_str(jsonvalue,'NodeId');
mcc_mnc_nw = get_field_num(jsonvalue,'NWMCCMNC');
mcc_mnc_sim = get_field_num(jsonvalue,'IMSIMCCMNC');

cnf_astream_algorithm = get_field_str(jsonvalue,'cnf_astream_algorithm');
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

res_yomo_buffer_mean = get_field_num(jsonvalue,'res_yomo_buffer_mean');
res_yomo_buffer_max = get_field_num(jsonvalue,'res_yomo_buffer_max');
res_yomo_buffer_min = get_field_num(jsonvalue,'res_yomo_buffer_min');
res_yomo_buffer_q1 = get_field_num(jsonvalue,'res_yomo_buffer_q1');
res_yomo_buffer_q2 = get_field_num(jsonvalue,'res_yomo_buffer_q2');
res_yomo_buffer_q3 = get_field_num(jsonvalue,'res_yomo_buffer_q3');
res_yomo_buffer_q4 = get_field_num(jsonvalue,'res_yomo_buffer_q4');

res_astream_buffer_mean = get_field_num(jsonvalue,'res_astream_buffer_mean');
res_astream_buffer_max = get_field_num(jsonvalue,'res_astream_buffer_max');
res_astream_buffer_min = get_field_num(jsonvalue,'res_astream_buffer_min');
res_astream_buffer_q1 = get_field_num(jsonvalue,'res_astream_buffer_q1');
res_astream_buffer_q2 = get_field_num(jsonvalue,'res_astream_buffer_q2');
res_astream_buffer_q3 = get_field_num(jsonvalue,'res_astream_buffer_q3');
res_astream_buffer_q4 = get_field_num(jsonvalue,'res_astream_buffer_q4');

res_yomo_numstalls = get_field_num(jsonvalue,'res_yomo_numstalls');
res_yomo_durstalls_mean = get_field_num(jsonvalue,'res_yomo_durstalls_mean');
res_yomo_durstalls_max = get_field_num(jsonvalue,'res_yomo_durstalls_max');
res_yomo_durstalls_min = get_field_num(jsonvalue,'res_yomo_durstalls_min');
res_yomo_durstalls_q1 = get_field_num(jsonvalue,'res_yomo_durstalls_q1');
res_yomo_durstalls_q2 = get_field_num(jsonvalue,'res_yomo_durstalls_q2');
res_yomo_durstalls_q3 = get_field_num(jsonvalue,'res_yomo_durstalls_q3');
res_yomo_durstalls_q4 = get_field_num(jsonvalue,'res_yomo_durstalls_q4');

res_astream_numstalls = get_field_num(jsonvalue,'res_astream_numstalls');
res_astream_durstalls_mean = get_field_num(jsonvalue,'res_astream_durstalls_mean');
res_astream_durstalls_max = get_field_num(jsonvalue,'res_astream_durstalls_max');
res_astream_durstalls_min = get_field_num(jsonvalue,'res_astream_durstalls_min');
res_astream_durstalls_q1 = get_field_num(jsonvalue,'res_astream_durstalls_q1');
res_astream_durstalls_q2 = get_field_num(jsonvalue,'res_astream_durstalls_q2');
res_astream_durstalls_q3 = get_field_num(jsonvalue,'res_astream_durstalls_q3');
res_astream_durstalls_q4 = get_field_num(jsonvalue,'res_astream_durstalls_q4');

res_yomo_numswitches_up = get_field_num(jsonvalue,'res_yomo_numswitches_up');
res_yomo_numswitches_down = get_field_num(jsonvalue,'res_yomo_numswitches_down');
res_astream_numswitches_up = get_field_num(jsonvalue,'res_astream_numswitches_up');
res_astream_numswitches_down = get_field_num(jsonvalue,'res_astream_numswitches_down');

%% Plots

% Figure window

close all
f = figure;
set(gcf, 'Position', [0, 0, 1500, 1000])

% Quantiles

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

% Subplot: bitrate

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

if size(yomo_stacked,1)==size(astream_stacked,1)
    subplot('Position',pos_bitrate)
    %bar([yomo_stacked,astream_stacked])
    bar([astream_stacked,yomo_stacked])
    
    xticklabels({'mean','max','min',str_q1,str_q2,str_q3,str_q4});
    %h = legend('YoMo','AStream');
    h = legend('AStream','YoMo');
    
    legend('show')
    set(gca,'FontSize',font_size)
    %set(h,'FontSize',font_size)
    
    title_str = 'Bitrate (Kbit/s)';
    title(title_str);
end

% Subplot: buffer

yomo_stacked = [res_yomo_buffer_mean;
    res_yomo_buffer_max;
    res_yomo_buffer_min;
    res_yomo_buffer_q1;
    res_yomo_buffer_q2;
    res_yomo_buffer_q3;
    res_yomo_buffer_q4];

astream_stacked = [res_astream_buffer_mean;
    res_astream_buffer_max;
    res_astream_buffer_min;
    res_astream_buffer_q1;
    res_astream_buffer_q2;
    res_astream_buffer_q3;
    res_astream_buffer_q4];

if size(yomo_stacked,1)==size(astream_stacked,1)
    subplot('Position',pos_buffer)
    %bar([yomo_stacked,astream_stacked])
    bar([astream_stacked,yomo_stacked])
    
    xticklabels({'mean','max','min',str_q1,str_q2,str_q3,str_q4});
    %h = legend('YoMo','AStream');
    h = legend('AStream','YoMo');
    
    legend('show')
    set(gca,'FontSize',font_size)
    set(h,'FontSize',font_size)
    
    title_str = 'Buffer (s)';
    title(title_str);
end

% Subplot: duration of stalls

yomo_stacked = [res_yomo_durstalls_mean;
    res_yomo_durstalls_max;
    res_yomo_durstalls_min;
    res_yomo_durstalls_q1;
    res_yomo_durstalls_q2;
    res_yomo_durstalls_q3;
    res_yomo_durstalls_q4];

astream_stacked = [res_astream_durstalls_mean;
    res_astream_durstalls_max;
    res_astream_durstalls_min;
    res_astream_durstalls_q1;
    res_astream_durstalls_q2;
    res_astream_durstalls_q3;
    res_astream_durstalls_q4];

if size(yomo_stacked,1)==size(astream_stacked,1)
    subplot('Position',pos_durstalls)
    %bar([yomo_stacked,astream_stacked])
    bar([astream_stacked,yomo_stacked])
    
    xticklabels({'mean','max','min',str_q1,str_q2,str_q3,str_q4});
    %h = legend('YoMo','AStream');
    h = legend('AStream','YoMo');
    
    legend('show')
    set(gca,'FontSize',font_size)
    set(h,'FontSize',font_size)
    
    title_str = 'Duration of Stalls (s)';
    title(title_str);
end

% Subplot: number of switches

yomo_stacked = [res_yomo_numswitches_up;
    res_yomo_numswitches_down]

astream_stacked = [res_astream_numswitches_up;
    res_astream_numswitches_down]

if size(yomo_stacked,1)==size(astream_stacked,1)
    subplot('Position',pos_numswitches)
    %bar([yomo_stacked,astream_stacked])
    bar([astream_stacked,yomo_stacked])
    
    xticklabels({'up','down'});
    %h = legend('YoMo','AStream');
    h = legend('AStream','YoMo');
    
    legend('show')
    set(gca,'FontSize',font_size)
    set(h,'FontSize',font_size)
    
    title_str = 'Number of Switches';
    title(title_str);
end

% Subplot: description

descr_bitrates = strsplit(res_astream_available_bitrates,bitrates_delimiter);

descr = {['Time: ',timestamp],...
    ['Container Version: ',container_version],...
    '',...
    ['Node ID: ',node_id],...
    ['MCCMNC (SIM): ',num2str(mcc_mnc_sim)],...
    ['MCCMNC (NW): ',num2str(mcc_mnc_nw)],...
    '',...
    ['AStream Algorithm: ',num2str(cnf_astream_algorithm)],...
    ['AStream Segment Limit: ',num2str(cnf_astream_segment_limit)],...
    ['YoMo Playback Duration: ',num2str(cnf_yomo_playback_duration_s)],...
    '',...
    ['Number of Stalls (AStream): ',num2str(res_astream_numstalls)],...
    ['Number of Stalls (YoMo): ',num2str(res_yomo_numstalls)],...
    '',...
    'Available Bitrates (bit/s): ',descr_bitrates{2:end}
    };

subplot('Position',pos_description)
t = text(textbox_x,textbox_y,descr);
t.FontSize = font_size;

axis off

%% Writing Output

mkdir(outdir);
outfile = strcat(campaign_tag,'_',foldername,'_',timestamp,'.jpg');
saveas(f,strcat(outdir,'/',outfile));

end

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
        if strcmp(value_str,'NA') || strcmp(value_str,'None') || isempty(value_str) || strcmp(value_str,'NaN')
            num_out = NaN;
        else
            num_out = str2num(value_str);
        end
        
    elseif isnumeric(value_str)
        num_out = value_str;
    end
catch ME
    disp(ME)
    num_out = NaN;
end
end