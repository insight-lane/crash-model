# Count Data Model for Crashes
# Developed by: Youshe Li, Ben Batorsky

library(MASS)
library(pscl)
library(AER)

mydata<- read.csv("crash_concern_street_counts_3.csv")
# Code as factors
mydata$Num_Lanes <- factor(mydata$Num_Lanes)
mydata$Surface_Tp <- factor(mydata$Surface_Tp)
mydata$Surface_Wd <- factor(mydata$Surface_Wd)
str(mydata)
attach(mydata)

# Define variables
Y <- cbind(nCrashes)
# Daily traffic, number of concerns, speed limit, 
# number lanes, surface type, surface width
X <- cbind(AADT, nConcerns, Speed_Limits, Num_Lanes, Surface_Tp, Surface_Wd)
X1 <- X

# Descriptive statistics
summary(Y)
summary(X)

# Poisson model 
poisson <- glm(Y ~ X, family="poisson")
summary(poisson)

# Negative binomial model 
negbin <- glm.nb(Y ~ X)
summary(negbin)

# Hurdle or truncated Poisson model 
hpoisson <- hurdle(Y ~ X | X1, link = "logit", dist = "poisson")
summary(hpoisson)

# Hurdle or truncated negative binonomial model 
hnegbin <- hurdle(Y ~ X | X1, link = "logit", dist = "negbin")
summary(hnegbin)

# Zero-inflated Poisson model 
zip <- zeroinfl(Y ~ X | X1, link = "logit", dist = "poisson")
summary(zip)

# Zero-inflated negative binomial model 
zinb <- zeroinfl(Y ~ X | X1, link = "logit", dist = "negbin")
summary(zinb)

#Diagnostics
#Vuong for testing benefit of using zero-inflation
vuong(negbin, zinb)
vuong(poisson,zip)
#AIC for everything else
AIC(zip, zinb, hpoisson, hnegbin)


#Look at differences with chosen model
observed_fitted_crash <- data.frame(
  zinb$y, 
  fitted(zinb), 
  residuals(zinb, 'response'))
#Fit bins
fit_bins<-data.frame(
  table(
    cut(observed_fitted_crash$fitted.zinb., c(0,1,2,3,4))
    )
  )

#Nice plot for comparison of models
library(ggplot2)
library(grid)
base <- ggplot(data=observed_fitted_crash, 
       aes(zinb.y))
bin_breaks <- stat_bin(bins=5, breaks=c(0,1,2,3,4))
fit_line <- geom_line(data=fit_bins,
                   aes(x=Var1, y=Freq, group=1))

p1 <- stat_bin(data=observed_fitted_crash, 
             aes(zinb.y, color='actual'), 
             bins=5, breaks=c(0,1,2,3,4))
p2<- stat_bin(data=observed_fitted_crash, 
       aes(fitted.zinb.,color='predicted'), 
       bins=5, breaks=c(0,1,2,3,4),
       geom='line',
       size=2)
p3<- stat_bin(data=observed_fitted_crash, 
              aes(fitted.zinb., color='predicted'), 
              bins=5, breaks=c(0,1,2,3,4),
              geom='point',
              size=3)
ggplot()+
  p1+p2+p3+
  theme_classic()+
  labs(x='Crash category', y='Frequency')+
  scale_color_manual(name='',
                     values=c(actual='black', predicted='red'))
