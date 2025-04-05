from django.db import models
from django.core.exceptions import ValidationError


class Tournament(models.Model):
    STATUS_CHOICES = [
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
    ]
    
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ONGOING'
    )
    groups = models.ManyToManyField('Group', through='TournamentGroup')

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date must be after start date")
        
        if self.status == 'COMPLETED' and not self.end_date:
            raise ValidationError("End date must be set when tournament is completed")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Player(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class TournamentGroup(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['tournament', 'group']

    def __str__(self):
        return f"{self.group.name} in {self.tournament.name}"


class Team(models.Model):
    player1 = models.ForeignKey(
        Player, related_name="teams_as_player1", on_delete=models.CASCADE
    )
    player2 = models.ForeignKey(
        Player, related_name="teams_as_player2", on_delete=models.CASCADE
    )
    tournament_group = models.ForeignKey(
        TournamentGroup, 
        related_name="teams", 
        on_delete=models.CASCADE,
    )
    rank = models.IntegerField(null=True, blank=True)
    is_withdrawn = models.BooleanField(default=False)

    class Meta:
        unique_together = ["player1", "player2", "tournament_group"]
        ordering = ["tournament_group", "rank"]

    def clean(self):
        if self.player1 == self.player2:
            raise ValidationError("A team must consist of two different players")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.player1.first_name}/{self.player2.first_name}"


class Match(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        related_name="matches",
        on_delete=models.CASCADE,
    )
    team1 = models.ForeignKey(
        Team, related_name="team1_matches", on_delete=models.CASCADE
    )
    team2 = models.ForeignKey(
        Team, related_name="team2_matches", on_delete=models.CASCADE
    )
    set1_team1 = models.IntegerField()
    set1_team2 = models.IntegerField()
    set2_team1 = models.IntegerField()
    set2_team2 = models.IntegerField()
    set3_team1 = models.IntegerField(null=True, blank=True)
    set3_team2 = models.IntegerField(null=True, blank=True)
    date_played = models.DateField(null=True, blank=True)

    def clean(self):
        if self.team1.tournament_group != self.team2.tournament_group:
            raise ValidationError("Teams must be in the same tournament group")

        if self.team1.tournament_group.tournament != self.tournament or \
           self.team2.tournament_group.tournament != self.tournament:
            raise ValidationError("Teams must belong to the tournament's groups")

        if self.date_played:
            if self.date_played < self.tournament.start_date:
                raise ValidationError("Match cannot be played before tournament start date")
            if self.tournament.end_date and self.date_played > self.tournament.end_date:
                raise ValidationError("Match cannot be played after tournament end date")

        sets = [(self.set1_team1, self.set1_team2), (self.set2_team1, self.set2_team2)]
        if self.set3_team1 is not None and self.set3_team2 is not None:
            sets.append((self.set3_team1, self.set3_team2))

        sets_won_team1 = sum(1 for set in sets if set[0] > set[1])
        sets_won_team2 = sum(1 for set in sets if set[1] > set[0])

        if sets_won_team1 + sets_won_team2 != len(sets):
            raise ValidationError("Each set must have a clear winner")

        if len(sets) == 2 and sets_won_team1 == sets_won_team2:
            raise ValidationError("Match must have a clear winner after two sets")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.team1} vs {self.team2} ({self.tournament})"

    def get_score(self):
        sets = [(self.set1_team1, self.set1_team2), (self.set2_team1, self.set2_team2)]
        if self.set3_team1 is not None and self.set3_team2 is not None:
            sets.append((self.set3_team1, self.set3_team2))

        score_team1 = score_team2 = 1  # Both teams get 1 point for playing
        for set_score in sets:
            if set_score[0] > set_score[1]:
                score_team1 += 1
            else:
                score_team2 += 1

        # Extra point for the winner
        if score_team1 > score_team2:
            score_team1 += 1
        else:
            score_team2 += 1

        return f"{score_team1}-{score_team2}"