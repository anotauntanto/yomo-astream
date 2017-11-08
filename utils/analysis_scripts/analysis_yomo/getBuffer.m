function buffer = getBuffer( path )
    data = loadDataLogFile( path );
      
    endIndeces = find(data(:,3) == 0);
    tmp = find(arrayfun(@(x) data(x,2)==data(x,4), endIndeces)==1);
    if ~isempty(endIndeces) 
        endIndex = endIndeces(tmp(1));
    else 
        endIndex = size(data,1);
    end
   
    buffer = data(1:endIndex,:);
end