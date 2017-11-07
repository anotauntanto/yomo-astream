function buffer = getBuffer( path )
    data = loadDataLogFile( path );
      
    endIndeces = find(data(:,3) == 0);
    tmp = find(arrayfun(@(x) data(x,2)==data(x,4), endIndeces)==1);
    endIndex = endIndeces(tmp(1));
   
    buffer = data(1:endIndex,:);
end