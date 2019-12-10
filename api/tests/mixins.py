from mixer.backend.django import mixer


class WithMakeUser:
    def _make_user(
            self, kind, userkwargs={}, employexkwargs={}, profilekwargs={}):

        if kind not in ['employee', 'employer']:
            raise RuntimeError('Do you know what are you doing?')

        user = mixer.blend('auth.User', **userkwargs)
        user.set_password('pass1234')
        user.save()

        emptype = 'api.Employee' if kind == 'employee' else 'api.Employer'

        if kind == 'employee':
            employexkwargs.update({
                'user': user
            })

        emp = mixer.blend(emptype, **employexkwargs)
        emp.save()

        profilekwargs = profilekwargs.copy()
        profilekwargs.update({
            'user': user,
            kind: emp,
        })

        profile = mixer.blend('api.Profile', **profilekwargs)
        profile.save()

        return user, emp, profile


class WithMakeShift:
    def _make_shift(self, employer,
                    shiftkwargs={}, venuekwargs={}, poskwargs={}):

        venue = mixer.blend('api.Venue', employer=employer, **venuekwargs)

        if 'position' not in shiftkwargs:
            shiftkwargs['position'] = mixer.blend('api.Position', **poskwargs)

        shift = mixer.blend(
            'api.Shift',
            venue=venue,
            employer=employer,
            **shiftkwargs,)

        return shift, venue, shiftkwargs['position']
