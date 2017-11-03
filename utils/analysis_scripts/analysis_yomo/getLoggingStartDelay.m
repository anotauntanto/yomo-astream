function delay = getLoggingStartDelay( path )
    data = loadDataLogFile( path );
    delay = data(1,2);
end