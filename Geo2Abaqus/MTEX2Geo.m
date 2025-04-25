mtexdata titanium
ebsd = ebsd('indexed');
grains = calcGrains(ebsd);
G=gmshGeo(grains);

[grains,ebsd.grainId] = calcGrains(ebsd,'angle',15*degree);	% Compute grains
grains = smooth(grains,20);
% remove two pixel grains
ebsd(grains(grains.grainSize<=10)) = [];
[grains,ebsd.grainId,ebsd.mis2mean] = calcGrains(ebsd('indexed'),'angle',5*degree,'removeQuadruplePoints');
% grains = smooth(grains,50);
plot(grains)
G=gmshGeo(grains);
savegeo(G,'titanium.geo');
exportGrainProps(G, 'orientation')