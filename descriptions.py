class ScoreDescription:
    def __init__(self, scoreNum, scoreDesc, percentile):
        self.scoreNum = scoreNum
        self.scoreDesc = scoreDesc
        self.percentile = percentile

    def __repr__(self):
        beg = end = ''
        if 90 <= self.scoreNum <= 100:
            beg = f"Your home is <b>extremely resilient</b> to {self.scoreDesc}."
            end = "It ranks among the top 10% of properties."
        elif 70 <= self.scoreNum <= 89:
            beg = f"Your home is <b>very resilient</b> to {self.scoreDesc}."
            end = "It ranks among the top 30% of properties."
        elif 50 <= self.scoreNum <= 69:
            beg = f"Your home is <b>somewhat resilient</b> to {self.scoreDesc}."
            end = "It ranks just above the average property."
        elif 25 <= self.scoreNum <= 49:
            beg = f"Your home is <b>vulnerable</b> to {self.scoreDesc}."
            end = "It ranks just below the average property."
        elif 0 <= self.scoreNum <= 24:
            beg = f"Your home is <b>extremely vulnerable</b> to {self.scoreDesc}."
            end = "It ranks among the worst 10% of properties."

        # do we want to print the end string?
        if self.percentile == 1:
            return beg + " " + end
        else:
            return beg


class DescribeAvg:
    def __init__(self, result, average):
        self.compare = result / average

    def __repr__(self):
        if self.compare == 1:
            return "<b>You are about average!</b>"
        elif self.compare < 1:
            return "<b>You are below average!</b>"
        elif self.compare > 1:
            return "<b>You are above average!</b>"


class TempScoreDescription:
    def __init__(self, tempScore, threshold, future):
        self.tempScore = tempScore
        self.threshold = threshold
        self.future = future

    def __repr__(self):
        risk = round(self.future / 21, 2)
        risk = round(100 * (risk - 1))
        sentence = str(ScoreDescription(self.tempScore, 'climate change related heat risk', 0))
        sentence = sentence + "<br><ul>"
        sentence = sentence + (
            f"<li>Your extreme heat day temperature: {self.threshold}°+ F"
            f"<li>Historic: <b>4 extreme heat days</b> per year</li>"
            f"<li>Forecast: <b>{round(self.future)} extreme heat days</b> per year</li>"
            f"<li>Forecasted state average: 21 days per year. "
        )
        if risk == 0:
            sentence = sentence + f"You are <b>similar risk</b> to the state average</li></ul>"
        elif risk < 0:
            sentence = sentence + f"You are <b>{-1 * risk}% less</b> than the state average</li></ul>"
        elif risk > 0:
            sentence = sentence + f"You are <b>{risk}% more</b> than the state average</li></ul>"

        return sentence


class FireScoreDescription:
    def __init__(self, fireScore, acres):
        self.fireScore = fireScore
        self.acres = acres

    def __repr__(self):
        # divide by avg acres burned
        multiplier = round(self.acres / 57.92954073, 2)
        risk = round(100 * (multiplier - 1))
        sentence = str(ScoreDescription(self.fireScore, 'climate change related fire risks', 0))
        if risk == 0:
            sentence = sentence + f"<br><ul><li>You are close to the state average</li></ul>"
        elif risk < 0:
            sentence = sentence + f"<br><ul><li>You have <b>{-1 * risk}% less</b> risk than the state average</li></ul>"
        elif risk > 0:
            sentence = sentence + f"<br><ul><li>You have <b>{risk}% more</b> risk than the state average</li></ul>"

        return sentence


class DroughtScoreDescription:
    def __init__(self, droughtScore, future_historic):
        self.droughtScore = droughtScore
        self.future_historic = future_historic

    def __repr__(self):
        # divide by avg future/historic WASSI
        multiplier = round(self.future_historic / 1.214938292, 2)
        risk = round(100 * (multiplier - 1))
        change = round(100 * (self.future_historic - 1))
        sentence = str(ScoreDescription(self.droughtScore, 'climate change related water stress', 0))
        if change == 0:
            sentence = sentence + f"<br><ul><li>Your water stress is forecasted to <b>stay the same. </b></li>"
        elif change < 0:
            sentence = sentence + f"<br><ul><li>Your water stress is forecasted to <b>decrease by {-1 * change}%. </b></li>"
        elif change > 0:
            sentence = sentence + f"<br><ul><li>Your water stress is forecasted to <b>increase by {change}%</b>.</li>"

        if risk == 0:
            return sentence + f"<li>You are close to the state average.</li></ul>"
        elif risk < 0:
            return sentence + f"<li>You are <b>{-1 * risk}% less</b> than the state average.</li></ul>"
        elif risk > 0:
            return sentence + f"<li>You are <b>{risk}% more</b> than the state average.</li></ul>"


class CarbonScoreDescription:
    def __init__(self, carbonScore, tons):
        self.carbonScore = carbonScore
        self.tons = tons

    def __repr__(self):
        # divide by avg acres burned
        multiplier = round((self.tons / 44.84346629), 2)
        multiplier = round(100 * (multiplier - 1))
        if 0 <= self.carbonScore < 20:
            sentence = "Your household carbon footprint is <b>poor.</b><br>"
        elif 20 <= self.carbonScore < 40:
            sentence = "Your household carbon footprint is <b>below average.</b><br>"
        elif 40 <= self.carbonScore < 60:
            sentence = "Your household carbon footprint is <b>average.</b><br>"
        elif 60 <= self.carbonScore < 80:
            sentence = "Your household carbon footprint is <b>above average.</b><br>"
        elif 80 <= self.carbonScore <= 100:
            sentence = "Your household carbon footprint is <b>excellent.</b><br>"

        sentence = sentence + f"<ul><li>You average <b>{round(self.tons)} tons of CO2e</b> per year</li>"

        if multiplier == 0:
            return sentence + f"<li>You are <b>similar</b> to the state average!</li></ul>"
        elif multiplier < 0:
            return sentence + f"<li>You are <b>{-1 * multiplier}% less</b> than the state average!</li></ul>"
        elif multiplier > 0:
            return sentence + f"<li>You are <b>{multiplier}% more</b> than the state average!</li></ul>"
        return sentence
