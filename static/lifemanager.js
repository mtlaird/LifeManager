// function GetTagTypes() {
//     fetch('/api/1/tag_types').then(function(response) {
//         return response.json(); }).then(function(myJson) {
//             console.log(myJson);
//     })
// }
//
// function GetTagsByType(type) {
//     const api_url = '/api/1/tag_types/' + type + '/tags';
//     fetch(api_url).then(function(response) {
//         return response.json(); }).then(function(myJson) {
//             console.log(myJson);
//     })
// }

function PopulateDataListWithTagValues(TargetList, TagType) {
    const api_url = '/api/1/tag_types/' + TagType + '/tags';
    fetch(api_url).then(function(response) {
        if (TagType.length === 0) return null;
        if (response.status === 200) return response.json(); }).then(function(myJson) {
            let dl = document.getElementById(TargetList);
            while (dl.firstChild) {
                dl.removeChild(dl.firstChild);
            }
            for (let tv in myJson) {
                let option = document.createElement("option");
                option.value=myJson[tv];
                dl.appendChild(option);
            }
    })
}

function makeObjectMapFromTableHeader(tableId) {
	var t = document.getElementById(tableId);
	var tHead = t.getElementsByTagName('thead')[0];
	var retArray = [];
	for (i = 0; cell = tHead.rows[0].cells[i];i++) {
		retArray.push(cell.innerHTML);
		}
	return retArray;
	}

function makeArrayFromTable(tableId) {
	var t = document.getElementById(tableId);
	var tBody = t.getElementsByTagName('tbody')[0];
	var tableMap = makeObjectMapFromTableHeader(tableId);
	var retArray = [], temp;
	for (var i = 0, row; row =tBody.rows[i]; i++) {
		temp = {};
		temp['display'] = row.style.display;
		for (var j = 0, cell; cell = row.cells[j]; j++) {
			temp[tableMap[j]] = cell.innerHTML;
			temp[tableMap[j]+'Text'] = cell.textContent;
			}
		retArray.push(temp);
		}
	return retArray;
	}

function makeTableFromArray(tableId,sourceArray) {
	var t = document.getElementById(tableId);
	var tBody = t.getElementsByTagName('tbody')[0], r, c;
	var tableMap = makeObjectMapFromTableHeader(tableId);
	for (var i = 0, row; row = tBody.rows[i]; i=i) {
		tBody.deleteRow(i);
		}
	for (i = 0; i < sourceArray.length; i++) {
		r = tBody.insertRow(i);
		for (var j = 0; j < tableMap.length; j++) {
			c = r.insertCell(j);
			c.innerHTML = sourceArray[i][tableMap[j]];
			}
		r.style.display = sourceArray[i]['display'];
		}
	}

function compareRows(sortType,sortOrder) {
	return function(a,b) {
		if (((a[sortType+'Text'].toUpperCase() > b[sortType+'Text'].toUpperCase()) && (sortOrder == 'Ascending')) || ((a[sortType+'Text'] < b[sortType+'Text']) && (sortOrder == 'Descending')))
			return 1;
		else if (((a[sortType+'Text'].toUpperCase() < b[sortType+'Text'].toUpperCase()) && (sortOrder == 'Ascending')) || ((a[sortType+'Text'].toUpperCase() > b[sortType+'Text'].toUpperCase()) && (sortOrder == 'Descending')))
			return -1;
		else return 0;
		}
	}

function compareDateRows(sortType,sortOrder) {
	return function(a,b) {
		aDate = new Date(a[sortType+'Text']);
		bDate = new Date(b[sortType+'Text']);
		if (((aDate > bDate) && (sortOrder == 'Ascending')) || ((aDate < bDate) && (sortOrder == 'Descending')))
			return 1;
		else if (((aDate < bDate) && (sortOrder == 'Ascending')) || ((aDate > bDate) && (sortOrder == 'Descending')))
			return -1;
		else return 0;
		}
	}

function compareVersionRows(sortType,sortOrder) {
	return function(a,b) {
		aVersion = parseInt(a[sortType].replace(".",""));
		bVersion = parseInt(b[sortType].replace(".",""));
		if (((aVersion > bVersion) && (sortOrder == 'Ascending')) || ((aVersion < bVersion) && (sortOrder == 'Descending')))
			return 1;
		else if (((aVersion < bVersion) && (sortOrder == 'Ascending')) || ((aVersion > bVersion) && (sortOrder == 'Descending')))
			return -1;
		else return 0;
		}
	}

function sortTable(tableId,sortType,sortOrder,buttonId) {
	a = makeArrayFromTable(tableId);
	if ( sortType == 'Date')
		a.sort(compareDateRows(sortType,sortOrder));
	else if ( sortType == 'Version')
		a.sort(compareVersionRows(sortType,sortOrder));
	else a.sort(compareRows(sortType,sortOrder));
	makeTableFromArray(tableId,a);
//	setTableRowAltClass(tableId);
	if (sortOrder == 'Ascending')
		document.getElementById(buttonId).onclick = function () { return sortTable(tableId,sortType,'Descending',buttonId); };
	else if (sortOrder == 'Descending')
		document.getElementById(buttonId).onclick = function () { return sortTable(tableId,sortType,'Ascending',buttonId); };
	}