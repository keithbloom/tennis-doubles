document.addEventListener('DOMContentLoaded', function() {
    const tournamentSelect = document.getElementById('id_tournament');
    const team1Select = document.getElementById('id_team1');
    const team2Select = document.getElementById('id_team2');

    function createGroupOption(groupName) {
        const optgroup = document.createElement('optgroup');
        optgroup.label = groupName;
        return optgroup;
    }

    function clearSelect(select) {
        const currentValue = select.value;  // Store current value before clearing
        select.innerHTML = '';
        const emptyOption = document.createElement('option');
        emptyOption.value = '';
        emptyOption.textContent = '---------';
        select.appendChild(emptyOption);
        return currentValue;  // Return the value that was selected
    }

    function syncTeamSelects() {
        // Get selected group from team1 (if any)
        const team1Selected = team1Select.options[team1Select.selectedIndex];
        if (team1Selected && team1Selected.closest('optgroup')) {
            const selectedGroup = team1Selected.closest('optgroup').label;
            
            // Hide all options in team2 except those from the same group
            Array.from(team2Select.getElementsByTagName('option')).forEach(option => {
                const optgroup = option.closest('optgroup');
                if (optgroup) {
                    option.hidden = optgroup.label !== selectedGroup;
                }
            });
        } else {
            // Show all options if no team is selected
            Array.from(team2Select.getElementsByTagName('option')).forEach(option => {
                option.hidden = false;
            });
        }
    }

    async function updateTeams() {
        const tournamentId = tournamentSelect.value;
        
        // Store current values before clearing
        const currentTeam1 = team1Select.value;
        const currentTeam2 = team2Select.value;
        
        clearSelect(team1Select);
        clearSelect(team2Select);

        if (!tournamentId) {
            return;
        }

        try {
            const response = await fetch(`/api/tournament/teams/?tournament=${tournamentId}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const groups = await response.json();
            
            groups.forEach(group => {
                const team1Group = createGroupOption(group.name);
                const team2Group = createGroupOption(group.name);
                
                group.teams.forEach(team => {
                    const team1Option = document.createElement('option');
                    team1Option.value = team.id;
                    team1Option.textContent = team.name;
                    if (team.id.toString() === currentTeam1) {
                        team1Option.selected = true;
                    }
                    team1Group.appendChild(team1Option);

                    const team2Option = document.createElement('option');
                    team2Option.value = team.id;
                    team2Option.textContent = team.name;
                    if (team.id.toString() === currentTeam2) {
                        team2Option.selected = true;
                    }
                    team2Group.appendChild(team2Option);
                });

                team1Select.appendChild(team1Group);
                team2Select.appendChild(team2Group);
            });

            syncTeamSelects();
        } catch (error) {
            console.error('Error fetching teams:', error);
        }
    }

    // Add event listeners
    tournamentSelect.addEventListener('change', updateTeams);
    team1Select.addEventListener('change', syncTeamSelects);

    // Initialize teams if tournament is already selected
    if (tournamentSelect.value) {
        updateTeams();
    }
});