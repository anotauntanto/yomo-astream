function [M] = loadEventLogFile( path )
%loadDataLogFile expects a String of the full path to the relevant logfile.
%   Example Path: path = 'C:\SmartQoE\Data\rRoA9MKqcD'
%   --> rRoA9MKqcD matches the objectId of the logfile
%   The result is a Matrix with a column for each of the logfile's columns
    p = fopen(path);
    M = textscan(p, '%f %s', 'delimiter', '#');
    fclose('all');
end