document.addEventListener('DOMContentLoaded', function() {
    const player1Select = document.getElementById('id_player1');
    const player2Select = document.getElementById('id_player2');

    if (!player1Select || !player2Select) {
        return;
    }

    // Function to get and set previous partner
    async function setPreviousPartner() {
        const player1Id = player1Select.value;

        // Only proceed if player1 is selected
        if (!player1Id) {
            return;
        }

        // Don't auto-fill if player2 is already set (e.g., when editing existing team)
        // Only auto-fill on new teams or when player2 is empty
        if (player2Select.value) {
            return;
        }

        try {
            const response = await fetch(`/api/tournament/previous-partner/?player_id=${player1Id}`);
            if (!response.ok) {
                console.error('Error fetching previous partner:', response.statusText);
                return;
            }

            const data = await response.json();
            if (data.partner_id) {
                // Set player2 to the previous partner
                player2Select.value = data.partner_id;
            }
        } catch (error) {
            console.error('Error fetching previous partner:', error);
        }
    }

    // Add event listener to player1 select
    player1Select.addEventListener('change', setPreviousPartner);
});
